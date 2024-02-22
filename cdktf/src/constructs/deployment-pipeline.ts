import path = require('path');
import { readFileSync } from 'fs';
import {
  cloudwatchLogGroup as cloudwatchLogGroupLib,
  cloudwatchEventRule,
  cloudwatchEventTarget,
  codebuildProject as codebuildProjectLib,
  ecrRepository,
  iamRole,
  subnet,
  vpc as vpcLib
} from '@cdktf/provider-aws';
import { Construct } from 'constructs';
import { DefaultedBaseConstructConfig } from '../configs';
import { truncate } from '../utils';

import CloudwatchEventRule = cloudwatchEventRule.CloudwatchEventRule;
import CloudwatchEventTarget = cloudwatchEventTarget.CloudwatchEventTarget;
import CodebuildProject = codebuildProjectLib.CodebuildProject;
import CloudwatchLogGroup = cloudwatchLogGroupLib.CloudwatchLogGroup;
import EcrRepository = ecrRepository.EcrRepository;
import IamRole = iamRole.IamRole;
import Subnet = subnet.Subnet;
import Vpc = vpcLib.Vpc;


/**
 * Config for the DeploymentPipeline construct
 */
export type DeploymentPipelineConfig = {
  /**
   * Whether to deploy the newly built image immediately after it is built.
   * @default - false
   */
  deployAfterBuild?: boolean;
  /**
   * The ECR repository holding the image to deploy.
   */
  ecrRepo: EcrRepository;
  /**
   * Arn of the ECS Cluster that hosts the target service.
   */
  clusterArn: string;
  /**
   * Name of the ECS Cluster to deploy changes to.
   */
  clusterName: string;
  /**
   * Name of the ECS Service to deploy changes to.
   */
  serviceName: string;
  /**
   * The private subnets with a NAT to launch the codebuild jobs in.
   */
  subnets: Subnet[];
  /**
   * The VPC to launch the codebuild jobs in.
   */
  vpc: Vpc;
  /**
   * The number of tasks to set on the service on update.
   */
  taskCount?: number;
};

export class DeploymentPipeline extends Construct {
  private _deployRole: IamRole;
  private _deployLogs: CloudwatchLogGroup;
  private _deploy: CodebuildProject;

  constructor (scope: Construct, id: string, baseConfig: DefaultedBaseConstructConfig, deploymentPipelineConfig: DeploymentPipelineConfig) {
    super(scope, id);

    const {
      region,
      accountId,
      environment
    } = baseConfig;

    const {
      deployAfterBuild = false,
      ecrRepo,
      clusterArn,
      clusterName,
      serviceName,
      subnets,
      vpc,
      taskCount = 0
    } = deploymentPipelineConfig;

    this._deployLogs = new CloudwatchLogGroup(this, `${id}-deploy-logs`, {
      name: `/${serviceName}/${environment}/deploy`,
      retentionInDays: 180
    });

    const roleNamePostfix = `-${environment}-deploy-role`;
    const namePrefix = truncate(`${serviceName}`, (64 - roleNamePostfix.length));
    const roleName = `${namePrefix}${roleNamePostfix}`;
    this._deployRole = new IamRole(this, `${id}-deploy-role`, {
      name: roleName,
      assumeRolePolicy: JSON.stringify({
        Version: '2012-10-17',
        Statement: [{
          Effect: 'Allow',
          Principal: {
            Service: 'codebuild.amazonaws.com'
          },
          Action: 'sts:AssumeRole'
        }]
      }),
      inlinePolicy: [
        {
          name: 'ecs-deploy-access',
          policy: JSON.stringify({
            Version: '2012-10-17',
            Statement: [{
              Effect: 'Allow',
              Action: [
                'ecs:UpdateService'
              ],
              Resource: [
                `arn:aws:ecs:${region}:${accountId}:service/${clusterName}/${serviceName}`
              ]
            }]
          })
        },
        {
          name: 'cloudwatchlogs-access',
          policy: JSON.stringify({
            Version: '2012-10-17',
            Statement: [{
              Effect: 'Allow',
              Action: [
                'logs:CreateLogStream',
                'logs:PutLogEvents'
              ],
              Resource: [
                this.deployLogs.arn,
                `${this.deployLogs.arn}/*`,
                `${this.deployLogs.arn}:*`
              ]
            }]
          })
        },
        {
          name: 'ecr-read-write-access',
          policy: JSON.stringify({
            Version: '2012-10-17',
            Statement: [{
              Effect: 'Allow',
              Action: [
                'ecr:BatchCheckLayerAvailability',
                'ecr:CompleteLayerUpload',
                'ecr:GetAuthorizationToken',
                'ecr:InitiateLayerUpload',
                'ecr:PutImage',
                'ecr:UploadLayerPart'
              ],
              Resource: [
                ecrRepo.arn
              ]
            }]
          })
        },
        {
          name: 'vpc-access',
          policy: JSON.stringify({
            'Version': '2012-10-17',
            'Statement': [
              {
                'Effect': 'Allow',
                'Action': [
                  'ec2:CreateNetworkInterface',
                  'ec2:DescribeDhcpOptions',
                  'ec2:DescribeNetworkInterfaces',
                  'ec2:DeleteNetworkInterface',
                  'ec2:DescribeSubnets',
                  'ec2:DescribeSecurityGroups',
                  'ec2:DescribeVpcs'
                ],
                'Resource': '*'
              },
              {
                'Effect': 'Allow',
                'Action': [
                  'ec2:CreateNetworkInterfacePermission'
                ],
                'Resource': `arn:aws:ec2:${region}:${accountId}:network-interface/*`,
                'Condition': {
                  'StringEquals': {
                    'ec2:AuthorizedService': 'codebuild.amazonaws.com'
                  },
                  'ArnEquals': {
                    'ec2:Subnet': subnets.map(s => s.arn)
                  }
                }
              }
            ]
          })
        }
      ],
      description: `Role used by CodeBuild to deploy image updates to the ECS Service ${serviceName}`
    });

    /**
     * NOTE: You escape `${` in HCL with `$${`.
     * However in JS regex, you have to additionally escape `$$` with `$$$`.
     * My guess is they're using groovy under the hood or something,
     * not important; but that's why the escape replaces looks odd.
     */
    const buildspec = readFileSync(
      path.resolve(
        'guardrails-api/buildspecs/deploy.yml'
      )
    ).toString().replace(/\$\{/g, '$$${');
    this._deploy = new CodebuildProject(this, `${id}-deploy`, {
      name: `${serviceName}-${environment}-deploy`,
      queuedTimeout: 5,
      buildTimeout: 5,
      source: {
        buildspec,
        type: 'NO_SOURCE'
      },
      artifacts: {
        type: 'NO_ARTIFACTS'
      },
      environment: {
        computeType: 'BUILD_GENERAL1_SMALL',
        image: 'aws/codebuild/amazonlinux2-aarch64-standard:3.0',
        type: 'ARM_CONTAINER',
        // TODO: Update with Env Vars for deploy-spec
        environmentVariable: [
          {
            name: 'ECR_ENDPOINT',
            value: ecrRepo.repositoryUrl
          },
          {
            name: 'IMAGE_VERSION_TAG',
            value: 'latest'
          },
          {
            name: 'CLUSTER_ARN',
            value: clusterArn
          },
          {
            name: 'ECS_CLUSTER_NAME',
            value: clusterName
          },
          {
            name: 'ECS_SERVICE_NAME',
            value: serviceName
          },
          {
            name: 'TASK_COUNT',
            value: taskCount.toString()
          }
        ]
      },
      serviceRole: this.deployRole.arn,
      logsConfig: {
        cloudwatchLogs: {
          groupName: this.deployLogs.name,
          status: 'ENABLED'
        }
      },
      vpcConfig: {
        vpcId: vpc.id,
        securityGroupIds: [vpc.defaultSecurityGroupId],
        subnets: subnets.map(s => s.id)
      }
    });

    const onPublishServiceRole = new IamRole(this, `${id}-deploy-pub-role`, {
      name: truncate(`${serviceName}-${environment}-deploy-rule-role`, 64),
      assumeRolePolicy: JSON.stringify({
        Version: '2012-10-17',
        Statement: [{
          Effect: 'Allow',
          Principal: {
            Service: 'events.amazonaws.com'
          },
          Action: 'sts:AssumeRole'
        }]
      }),
      inlinePolicy: [
        {
          name: 'deploy-job-access',
          policy: JSON.stringify({
            Version: '2012-10-17',
            Statement: [
              {
                Effect: 'Allow',
                Action: [
                  'codebuild:StartBuild'
                ],
                Resource: [
                  this.deploy.arn
                ]
              }
            ]
          })
        }
      ],
      description: `Role used by EventBridge to trigger actions for ${serviceName}-${environment}-deploy-rule`
    });
    const onPublishRule = new CloudwatchEventRule(this, `${id}-deploy-pub-rule`, {
      name: truncate(`${serviceName}-${environment}-deploy-rule`, 64),
      description: `Starts ${serviceName}-${environment}-deploy when an image is published to ${ecrRepo.name}`,
      isEnabled: deployAfterBuild,
      eventPattern: JSON.stringify({
        'detail-type': [
          'ECR Image Action'
        ],
        'source': [
          'aws.ecr'
        ],
        'detail': {
          'action-type': [
            'PUSH'
          ],
          'image-tag': [
            'latest'
          ],
          'repository-name': [
            ecrRepo.name
          ],
          'result': [
            'SUCCESS'
          ]
        }
      }),
      roleArn: onPublishServiceRole.arn
    });
    new CloudwatchEventTarget(this, `${id}-deploy-pub-target`, {
      arn: this.deploy.arn,
      rule: onPublishRule.name,
      roleArn: onPublishServiceRole.arn
    });
  }

  public get deployRole (): IamRole {
    return this._deployRole;
  }
  public get deployLogs (): CloudwatchLogGroup {
    return this._deployLogs;
  }
  public get deploy (): CodebuildProject {
    return this._deploy;
  }

}