import { Construct } from 'constructs';
import { CloudwatchLogGroup } from '@cdktf/provider-aws/lib/cloudwatch-log-group';
import { IamRole, IamRoleInlinePolicy } from '@cdktf/provider-aws/lib/iam-role';
import { EcrRepository } from '@cdktf/provider-aws/lib/ecr-repository';
import { EcsTaskDefinition } from '@cdktf/provider-aws/lib/ecs-task-definition';
import { BaseConstructConfig } from '../../../../src/configs';
import { truncate } from '../utils';

export type NameValue = {
  name: string;
  value: string;
}

export type SecretRef = {
  name: string;
  valueFrom: string;
}

export type ContainerConfig = {
  image: string;
  name: string;
  port: number;
  environmentVariables?: NameValue[];
  secrets?: SecretRef[];
}

export type TaskConfig = BaseConstructConfig & {
  containers: ContainerConfig[];
  ecrRepo: EcrRepository;
  logGroup: CloudwatchLogGroup;
  serviceName: string;
  cpu?: number;
  memory?: number;
  taskPolicies?: IamRoleInlinePolicy[];
  executionPolicies?: IamRoleInlinePolicy[];
};

export class Task extends Construct {
  private _executionRole: IamRole;
  private _taskRole: IamRole;
  private _taskDefinition: EcsTaskDefinition;

  constructor (scope: Construct, id: string, config: TaskConfig) {
    super(scope, id);

    const {
      cpu = 256,
      ecrRepo,
      containers,
      logGroup,
      memory = 512,
      region,
      serviceName,
      taskPolicies = [],
      executionPolicies = []
    } = config;

    // Used by ECS to create tasks
    this._executionRole = new IamRole(this, `${id}-execution-role`, {
      name: `${truncate(`${serviceName}`, (64 - '-execution-role'.length))}-execution-role`,
      inlinePolicy: [
        ...executionPolicies,
        {
          name: 'allow-ecr-pull',
          policy: JSON.stringify({
            Version: '2012-10-17',
            Statement: [
              {
                Effect: 'Allow',
                Action: [
                  'ecr:GetAuthorizationToken',
                  'ecr:BatchCheckLayerAvailability',
                  'ecr:GetDownloadUrlForLayer',
                  'ecr:BatchGetImage',
                  'logs:CreateLogStream',
                  'logs:PutLogEvents'
                ],
                Resource: [
                  ecrRepo.arn
                ]
              }
            ]
          })
        }
      ],
      assumeRolePolicy: JSON.stringify({
        Version: '2012-10-17',
        Statement: [
          {
            Action: 'sts:AssumeRole',
            Effect: 'Allow',
            Principal: {
              Service: 'ecs-tasks.amazonaws.com'
            }
          }
        ]
      }),
      managedPolicyArns: [
        'arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy'
      ]
    });

    // Used by tasks to do stuff in the app
    this._taskRole = new IamRole(this, 'task-role', {
      name: `${truncate(`${serviceName}`, (64 - '-task-role'.length))}-task-role`,
      inlinePolicy: [
        ...taskPolicies,
        {
          name: 'allow-logs',
          policy: JSON.stringify({
            Version: '2012-10-17',
            Statement: [
              {
                Effect: 'Allow',
                Action: ['logs:CreateLogStream', 'logs:PutLogEvents'],
                Resource: [
                  logGroup.arn,
                  `${logGroup.arn}/*`,
                  `${logGroup.arn}:*`
                ]
              }
            ]
          })
        }
      ],
      assumeRolePolicy: JSON.stringify({
        Version: '2012-10-17',
        Statement: [
          {
            Action: 'sts:AssumeRole',
            Effect: 'Allow',
            Principal: {
              Service: 'ecs-tasks.amazonaws.com'
            }
          }
        ]
      })
    });

    const containerDefinitions =  containers.map(c => ({
      name: c.name,
      image: c.image,
      portMappings: [
        {
          containerPort: c.port
        }
      ],
      logConfiguration: {
        logDriver: 'awslogs',
        options: {
          'awslogs-region': region,
          'awslogs-group': logGroup.name,
          'awslogs-stream-prefix': c.name
        }
      },
      environment: c.environmentVariables,
      secrets: c.secrets
    }));

    this._taskDefinition = new EcsTaskDefinition(this, `${id}-task-definition`, {
      containerDefinitions: JSON.stringify(containerDefinitions),
      family: serviceName,
      cpu: cpu.toString(),
      memory: memory.toString(),
      requiresCompatibilities: ['FARGATE'],
      executionRoleArn: this._executionRole.arn,
      taskRoleArn: this._taskRole.arn,
      networkMode: 'awsvpc',
      runtimePlatform: {
        cpuArchitecture: 'ARM64',
        operatingSystemFamily: 'LINUX'
      }
    });
  }

  public get executionRole (): IamRole {
    return this._executionRole;
  }
  public get taskRole (): IamRole {
    return this._taskRole;
  }
  public get taskDefinition (): EcsTaskDefinition {
    return this._taskDefinition;
  }
}