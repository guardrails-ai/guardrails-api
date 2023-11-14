import { Construct } from 'constructs';
import {
  cloudwatchLogGroup as cloudwatchLogGroupLib,
  ecrRepository,
  iamRole,
  lambdaFunction as lambdaFunctionLib,
  lambdaFunctionUrl as lambdaFunctionUrlLib,
  subnet,
  vpc as vpcLib
} from '@cdktf/provider-aws';
import { DefaultedBaseConstructConfig, OpenSearchConfig } from '../configs';

import CloudwatchLogGroup = cloudwatchLogGroupLib.CloudwatchLogGroup;
import EcrRepository = ecrRepository.EcrRepository;
import IamRole = iamRole.IamRole;
import LambdaFunction = lambdaFunctionLib.LambdaFunction;
import LambdaFunctionUrl = lambdaFunctionUrlLib.LambdaFunctionUrl;
import Subnet = subnet.Subnet;
import Vpc = vpcLib.Vpc;
import { RdsPostgres } from './rds-postgres';

export type ApplicationConfig = {
  ecrRepo: EcrRepository;
  lambdaFunctionName: string;
  openSearchConfig: OpenSearchConfig;
  rdsPostgres: RdsPostgres;
  subnets: Subnet[];
  vpc: Vpc;
};

export class Application extends Construct {
  private _endpoint: string;
  private _lambdaFunction: LambdaFunction;
  private _lambdaRole: IamRole;
  private _lambdaUrl: LambdaFunctionUrl;
  private _lambdaLogs: CloudwatchLogGroup;

  constructor (scope: Construct, id: string, baseConfig: DefaultedBaseConstructConfig, applicationConfig: ApplicationConfig) {
    super(scope, id);

    const {
      environment
    } = baseConfig;

    const {
      ecrRepo,
      lambdaFunctionName,
      openSearchConfig,
      rdsPostgres,
      subnets,
      vpc
    } = applicationConfig;

    const {
      credentials: openSearchClusterCredentials,
      opensearchDomain,
      traceIngestionPipeline,
      logIngestionPipeline,
      metricIngestionPipeline
    } = openSearchConfig;

    this._lambdaLogs = new CloudwatchLogGroup(this, `${id}-lambda-logs`, {
      name: `/aws/lambda/${lambdaFunctionName}`,
      retentionInDays: 30
    });

    this._lambdaRole = new IamRole(this, `${id}-lambda-role`, {
      name: `${lambdaFunctionName}-role`,
      assumeRolePolicy: JSON.stringify({
        Version: '2012-10-17',
        Statement: [{
          Effect: 'Allow',
          Principal: {
            Service: 'lambda.amazonaws.com'
          },
          Action: 'sts:AssumeRole'
        }]
      }),
      inlinePolicy: [
        {
          name: 'opensearch-access',
          policy: JSON.stringify({
            Version: '2012-10-17',
            Statement: [{
              Effect: 'Allow',
              Action: [
                'es:ESHttp*'
              ],
              Resource: [
                opensearchDomain.arn,
                `${opensearchDomain.arn}/*`
              ]
            }]
          })
        },
        {
          name: 'secrets-manager-access',
          policy: JSON.stringify({
            Version: '2012-10-17',
            Statement: [{
              Effect: 'Allow',
              Action: [
                'secretsmanager:GetSecretValue'
              ],
              Resource: [
                openSearchClusterCredentials.arn,
                rdsPostgres.secretArn
              ]
            }]
          })
        },
        {
          name: 'eni-access',
          policy: JSON.stringify({
            Version: '2012-10-17',
            Statement: [{
              Effect: 'Allow',
              Action: [
                'ec2:CreateNetworkInterface',
                'ec2:DescribeNetworkInterfaces',
                'ec2:DeleteNetworkInterface'
              ],
              // Does not work without broad access
              Resource: '*'
            }]
          })
        },
        {
          name: 'cloudwatch-access',
          policy: JSON.stringify({
            Version: '2012-10-17',
            Statement: [{
              Effect: 'Allow',
              Action: [
                'logs:CreateLogGroup',
                'logs:CreateLogStream',
                'logs:PutLogEvents'
              ],
              Resource: [
                this.lambdaLogs.arn,
                `${this.lambdaLogs.arn}/*`,
                `${this.lambdaLogs.arn}:*`
              ]
            }]
          })
        },
        {
          name: 'ingestion-access',
          policy: JSON.stringify({
            Version: '2012-10-17',
            Statement: [
              {
                Effect: 'Allow',
                Action: ['osis:Ingest'],
                Resource: [
                  traceIngestionPipeline.arn,
                  metricIngestionPipeline.arn,
                  logIngestionPipeline.arn
                ]
              }
            ]
          })
        }
      ]
    });

    this._lambdaFunction = new LambdaFunction(this, `${id}-lambda-function`, {
      functionName: lambdaFunctionName,
      description: 'Guardrails Validation Service API',
      role: this.lambdaRole.arn,
      architectures: ['arm64'],
      environment: {
        variables: {
          APP_ENVIRONMENT: environment,
          AWS_LWA_READINESS_CHECK_PORT: '8000',
          LOGLEVEL: 'INFO',
          NODE_ENV: 'production',
          OPENSEARCH_SECRET: openSearchClusterCredentials.arn,
          OPENSEARCH_URL: opensearchDomain.endpoint,
          OTEL_SERVICE_NAME: 'guardrails-api',
          OTEL_TRACES_EXPORTER: 'otlp',
          OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST: 'Accept-Encoding,User-Agent,Referer',
          OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE: 'Last-Modified,Content-Type',
          OTEL_METRICS_EXPORTER: 'none',
          OTEL_TRACE_SINK: `https://${traceIngestionPipeline.endpoint}/traces/ingest`,
          OTEL_METRIC_SINK: `https://${metricIngestionPipeline.endpoint}/metrics/ingest`,
          OTEL_LOG_SINK: `https://${logIngestionPipeline.endpoint}/logs/ingest`,
          OPENTELEMETRY_COLLECTOR_CONFIG_FILE: 'app/configs/lambda-collector-config.yml',
          PGPORT: rdsPostgres.instance.port.toString(),
          PGDATABASE: rdsPostgres.instance.dbName,
          PGHOST: rdsPostgres.instance.endpoint,
          PGUSER: 'postgres',
          PGPASSWORD_SECRET_ARN: rdsPostgres.secretArn,
          PORT: '8000',
          PYTHONUNBUFFERED: '1'
        }
      },
      imageUri: `${ecrRepo.repositoryUrl}:latest`,
      memorySize: 512,
      packageType: 'Image',
      timeout: 60 * 15,
      vpcConfig: {
        securityGroupIds: [vpc.defaultSecurityGroupId],
        subnetIds: subnets.map(s => s.id)
      }
    });

    this._lambdaUrl = new LambdaFunctionUrl(this, `${id}-lambda-url`, {
      functionName: this.lambdaFunction.functionName,
      authorizationType: 'NONE'
    });
    this._endpoint = this.lambdaUrl.functionUrl;
  }

  public get endpoint (): string {
    return this._endpoint;
  }
  public get lambdaLogs (): CloudwatchLogGroup {
    return this._lambdaLogs;
  }
  public get lambdaRole (): IamRole {
    return this._lambdaRole;
  }
  public get lambdaFunction (): LambdaFunction {
    return this._lambdaFunction;
  }
  public get lambdaUrl (): LambdaFunctionUrl {
    return this._lambdaUrl;
  }
}