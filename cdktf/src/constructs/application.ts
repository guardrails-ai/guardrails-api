import { Construct } from 'constructs';
import {
  cloudwatchLogGroup as cloudwatchLogGroupLib,
  iamRole
} from '@cdktf/provider-aws';
import { OpenSearchConfig } from '../configs';

import CloudwatchLogGroup = cloudwatchLogGroupLib.CloudwatchLogGroup;
import IamRole = iamRole.IamRole;
import { RdsPostgres } from './rds-postgres';
import { ComputeService, ComputeServiceConfig as ComputeServiceConfigRequired } from './compute-service';
import { NameValue } from './task';
import { IamRoleInlinePolicy } from '@cdktf/provider-aws/lib/iam-role';

type ComputeServiceConfig = Omit<
  ComputeServiceConfigRequired,
  'containers'
>

export type ApplicationConfig = ComputeServiceConfig & {
  openSearchConfig: OpenSearchConfig;
  rdsPostgres: RdsPostgres;
  environmentVariables?: NameValue[];
};

export class Application extends Construct {
  private _endpoint: string;
  private _service: ComputeService;
  private _role: IamRole;
  private _logs: CloudwatchLogGroup;

  constructor(scope: Construct, id: string, config: ApplicationConfig) {
    super(scope, id);

    const {
      environment,
      ecrRepo,
      openSearchConfig,
      rdsPostgres,
      environmentVariables = [],
      taskPolicies = [],
      memory = 1024
    } = config;

    const {
      credentials: openSearchClusterCredentials,
      opensearchDomain,
      traceIngestionPipeline,
      logIngestionPipeline,
      metricIngestionPipeline
    } = openSearchConfig;

    const openSearchAccess: IamRoleInlinePolicy = {
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
    };
    const openSearchIngestionAccess: IamRoleInlinePolicy = {
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
    };
    const secretsManagerAccess: IamRoleInlinePolicy = {
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
    };
    
    taskPolicies.push(
      openSearchAccess,
      openSearchIngestionAccess,
      secretsManagerAccess
    )
    environmentVariables.push(...[
      {
        name: 'APP_ENVIRONMENT',
        value: environment
      },
      {
        name: 'AWS_LWA_READINESS_CHECK_PORT',
        value: '8000'
      },
      {
        name: 'LOGLEVEL',
        value: 'INFO'
      },
      {
        name: 'NODE_ENV',
        value: 'production'
      },
      {
        name: 'NLTK_DATA',
        value: '/opt/nltk_data'
      },
      {
        name: 'OPENSEARCH_SECRET',
        value: openSearchClusterCredentials.arn
      },
      {
        name: 'OPENSEARCH_URL',
        value: opensearchDomain.endpoint
      },
      {
        name: 'OTEL_SERVICE_NAME',
        value: 'guardrails-api'
      },
      {
        name: 'OTEL_TRACES_EXPORTER',
        value: 'otlp'
      },
      {
        name: 'OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST',
        value: 'Accept-Encoding,User-Agent,Referer'
      },
      {
        name: 'OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE',
        value: 'Last-Modified,Content-Type'
      },
      {
        name: 'OTEL_METRICS_EXPORTER',
        value: 'none'
      },
      {
        name: 'OTEL_TRACE_SINK',
        value: `https://${traceIngestionPipeline.endpoint}/traces/ingest`
      },
      {
        name: 'OTEL_METRIC_SINK',
        value: `https://${metricIngestionPipeline.endpoint}/metrics/ingest`
      },
      {
        name: 'OTEL_LOG_SINK',
        value: `https://${logIngestionPipeline.endpoint}/logs/ingest`
      },
      {
        name: 'OPENTELEMETRY_COLLECTOR_CONFIG_FILE',
        value: 'app/configs/lambda-collector-config.yml'
      },
      {
        name: 'PGPORT',
        value: rdsPostgres.instance.port.toString()
      },
      {
        name: 'PGDATABASE',
        value: rdsPostgres.instance.dbName
      },
      {
        name: 'PGHOST',
        value: rdsPostgres.instance.endpoint
      },
      {
        name: 'PGUSER',
        value: 'postgres'
      },
      {
        name: 'PGPASSWORD_SECRET_ARN',
        value: rdsPostgres.secretArn
      },
      {
        name: 'PORT',
        value: '8000'
      },
      {
        name: 'PYTHONUNBUFFERED',
        value: '1'
      }
    ])
    this._service = new ComputeService(this, `${id}-compute-service`, {
      ...config,
      containers: [{
        image: ecrRepo.repositoryUrl,
        name: ecrRepo.name,
        port: 8000,
        environmentVariables
      }],
      memory,
      taskPolicies
    });

    this._logs = this.service.logGroup;
    this._role = this.service.task.taskRole;
    this._endpoint = this.service.gateway.api.apiEndpoint;
  }

  public get endpoint(): string {
    return this._endpoint;
  }
  public get logs(): CloudwatchLogGroup {
    return this._logs;
  }
  public get role(): IamRole {
    return this._role;
  }
  public get service(): ComputeService {
    return this._service;
  }
}