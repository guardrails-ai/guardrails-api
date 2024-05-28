import { Construct } from 'constructs';
import {
  dataAwsCallerIdentity,
  dataAwsRegion,
  subnet,
  vpc as vpcLib
} from '@cdktf/provider-aws';
import { DefaultedBaseConstructConfig } from '../configs';
import {
  DeploymentPipeline,
  DeploymentPipelineConfig as DeploymentPipelineConfigRequired,
  RdsPostgres,
  RdsPostgresConfig as RdsPostgresConfigRequired
} from '../constructs';
import { truncate } from '../utils';

import AwsCallerIdentity = dataAwsCallerIdentity.DataAwsCallerIdentity;
import AwsRegion = dataAwsRegion.DataAwsRegion
import Subnet = subnet.Subnet;
import Vpc = vpcLib.Vpc;
import { EcsCluster } from '@cdktf/provider-aws/lib/ecs-cluster';
import { Apigatewayv2VpcLink } from '@cdktf/provider-aws/lib/apigatewayv2-vpc-link';
import { ServiceDiscoveryPrivateDnsNamespace } from '@cdktf/provider-aws/lib/service-discovery-private-dns-namespace';
import { EcrRepository } from '@cdktf/provider-aws/lib/ecr-repository';
import { ComputeService, ComputeServiceConfig } from '../constructs/compute-service';
import { IamRoleInlinePolicy } from '@cdktf/provider-aws/lib/iam-role';
import { NameValue } from '../constructs/task';

export type RdsPostgresConfig = Omit<RdsPostgresConfigRequired, 'name' | 'subnets' | 'vpc'>
export type DeploymentPipelineConfig = Omit<
  DeploymentPipelineConfigRequired,
  'ecrRepo' |
  'subnets' |
  'vpc' |
  'clusterArn' |
  'clusterName' |
  'serviceName'
>

export type OtelConfig = {
  /**
   * Sets the environment variable `OTEL_PYTHON_TRACER_PROVIDER`
   * Defaults to `sdk_tracer_provider`
   */
  pythonTracerProvider?: string;
  /**
   * Sets the environment variable `OTEL_SERVICE_NAME`
   * Defaults to `guardrails-api`
   */
  serviceName?: string;
  /**
   * Sets the environment variable `OTEL_TRACES_EXPORTER`
   * Defaults to `otlp`
   */
  tracesExporter?: string;
  /**
   * Sets the environment variable `OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST`
   * Defaults to `Accept-Encoding,User-Agent,Referer`
   */
  instrumentationHttpCaptureHeadersServerRequest?: string;
  /**
   * Sets the environment variable `OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE`
   * Defaults to `Last-Modified,Content-Type`
   */
  instrumentationHttpCaptureHeadersServerResponse?: string;
  /**
   * Sets the environment variable `OTEL_METRICS_EXPORTER`
   * Defaults to `none`
   */
  metricsExporter?: string;
  /**
   * Sets the environment variable `OTEL_EXPORTER_OTLP_PROTOCOL`
   * Defaults to `http/protobuf`
   */
  otlpProtocol?: string;
  /**
   * Sets the environment variable `OTEL_EXPORTER_OTLP_ENDPOINT`
   * Defaults to `http://localhost:4317`
   */
  otlpEndpoint?: string;
  /**
   * Sets the environment variable `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`
   * Defaults to `${otlpEndpoint}/v1/traces`
   */
  traceSink?: string;
  /**
   * Sets the environment variable `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT`
   * Defaults to `${otlpEndpoint}/v1/metrics`
   */
  metricsSink?: string;
  /**
   * Sets the environment variable `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`
   * Defaults to `${otlpEndpoint}/v1/logs`
   */
  logsSink?: string;
}

export type ServerConfig = Omit<ComputeServiceConfig,
  'containers' |
  'serviceName'
>

export type GuardrailsValidationServiceSubStackConfig = ServerConfig & {
  deploymentPipelineConfig: DeploymentPipelineConfig;
  ecrRepo: EcrRepository;
  rdsPostgresConfig?: RdsPostgresConfig;
  subnets: Subnet[];
  vpc: Vpc;
  cluster: EcsCluster;
  vpcLink: Apigatewayv2VpcLink;
  serviceDiscoveryNamespace: ServiceDiscoveryPrivateDnsNamespace;
  otelConfig?: OtelConfig;
  environmentVariables?: NameValue[];
}

export class GuardrailsValidationServiceSubStack extends Construct {
  private _pgDatabase: RdsPostgres;
  private _deploymentPipeline: DeploymentPipeline;
  private _server: ComputeService;

  constructor (scope: Construct, id: string, config: GuardrailsValidationServiceSubStackConfig) {
    super(scope, id);

    const currentIdentity = new AwsCallerIdentity(this, `${id}-aws-identity`);
    const defaultAccount: string = currentIdentity.accountId;
    const currentRegion = new AwsRegion(this, `${id}-aws-region`);
    const defaultRegion: string = currentRegion.name;

    const {
      accountId = defaultAccount,
      cluster,
      deploymentPipelineConfig,
      environment,
      ecrRepo,
      rdsPostgresConfig = {},
      region = defaultRegion,
      subnets,
      vpc,
      profile,
      environmentVariables = [],
      taskPolicies = [],
      memory = 1024,
      otelConfig = {}
    } = config;


    const {
      pythonTracerProvider = 'sdk_tracer_provider',
      serviceName: otelServiceName = 'guardrails-api',
      tracesExporter = 'otlp',
      instrumentationHttpCaptureHeadersServerRequest = 'Accept-Encoding,User-Agent,Referer',
      instrumentationHttpCaptureHeadersServerResponse = 'Last-Modified,Content-Type',
      metricsExporter = 'none',
      otlpProtocol = 'http/protobuf',
      otlpEndpoint = 'http://localhost:4317',
    } = otelConfig;
    const {
      traceSink = `${otlpEndpoint}/v1/traces`,
      metricsSink = `${otlpEndpoint}/v1/metrics`,
      logsSink = `${otlpEndpoint}/v1/logs`,
    } = otelConfig;
    
    const baseConfig: DefaultedBaseConstructConfig = {
      accountId,
      environment,
      profile,
      region
    };

    const baseName = `${id}-guardrails-validation-service`;
    const serviceName = truncate(`${baseName}-api-${environment}`, 59); // Allow 5 characters for appending `-role`
    const dbName = truncate(`${baseName}-postgres-db`, 59); // 63 -sg

    const deploymentPipelineConfigRequired: DeploymentPipelineConfigRequired = {
      ...deploymentPipelineConfig,
      ecrRepo,
      clusterArn: cluster.arn,
      clusterName: cluster.name,
      serviceName,
      vpc,
      subnets
    };
    const rdsPostgresConfigRequired: RdsPostgresConfigRequired = {
      ...rdsPostgresConfig,
      name: dbName,
      vpc,
      subnets
    };

    this._deploymentPipeline = new DeploymentPipeline(this, `${id}-ci-cd`, baseConfig, deploymentPipelineConfigRequired);

    this._pgDatabase = new RdsPostgres(this, `${id}-pg`, rdsPostgresConfigRequired)

    const pgSecretsManagerAccess: IamRoleInlinePolicy = {
      name: 'pg-secrets-manager-access',
      policy: JSON.stringify({
        Version: '2012-10-17',
        Statement: [{
          Effect: 'Allow',
          Action: [
            'secretsmanager:GetSecretValue'
          ],
          Resource: [
            this.pgDatabase.secretArn
          ]
        }]
      })
    };
    
    taskPolicies.push(
      pgSecretsManagerAccess
    );
    const mandatoryEnvVars = [
      {
        name: 'APP_ENVIRONMENT',
        value: environment
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
        name: 'PGPORT',
        value: this.pgDatabase.instance.port.toString()
      },
      {
        name: 'PGDATABASE',
        value: this.pgDatabase.instance.dbName
      },
      {
        name: 'PGHOST',
        value: this.pgDatabase.instance.endpoint
      },
      {
        name: 'PGUSER',
        value: 'postgres'
      },
      {
        name: 'PGPASSWORD_SECRET_ARN',
        value: this.pgDatabase.secretArn
      },
      {
        name: 'PORT',
        value: '8000'
      },
      {
        name: 'AWS_EXECUTION_ENV',
        value: 'AWS_ECS_Fargate'
      }
    ];
    const optionalEnvVars = [
      {
        name: 'PYTHONUNBUFFERED',
        value: '1'
      },
      {
        name: 'OTEL_PYTHON_TRACER_PROVIDER',
        value: pythonTracerProvider
      },
      {
        name: 'OTEL_SERVICE_NAME',
        value: otelServiceName
      },
      {
        name: 'OTEL_TRACES_EXPORTER',
        value: tracesExporter
      },
      {
        name: 'OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST',
        value: instrumentationHttpCaptureHeadersServerRequest
      },
      {
        name: 'OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE',
        value: instrumentationHttpCaptureHeadersServerResponse
      },
      {
        name: 'OTEL_METRICS_EXPORTER',
        value: metricsExporter
      },
      {
        name: 'OTEL_EXPORTER_OTLP_PROTOCOL',
        value: otlpProtocol
      },
      {
        name: 'OTEL_EXPORTER_OTLP_ENDPOINT',
        value: otlpEndpoint
      },
      {
        name: 'OTEL_EXPORTER_OTLP_TRACES_ENDPOINT',
        value: traceSink
      },
      {
        name: 'OTEL_EXPORTER_OTLP_METRICS_ENDPOINT',
        value: metricsSink
      },
      {
        name: 'OTEL_EXPORTER_OTLP_LOGS_ENDPOINT',
        value: logsSink
      },
      {
        name: 'LOG_LEVEL',
        value: 'DEBUG'
      }
    ];
    
    const mandatoryEnvVarNames: string[] = mandatoryEnvVars.map(ev => ev.name);
    const userEnvVarNames: string[] = environmentVariables.map(ev => ev.name);
    mandatoryEnvVars.push(
      ...environmentVariables.filter((envVar: NameValue) => !mandatoryEnvVarNames.includes(envVar.name)),
      ...optionalEnvVars.filter((envVar: NameValue) => !userEnvVarNames.includes(envVar.name))
    );
    environmentVariables;
    this._server = new ComputeService(this, `${id}-compute-service`, {
      ...config,
      containers: [{
        image: ecrRepo.repositoryUrl,
        name: ecrRepo.name,
        port: 8000,
        environmentVariables: mandatoryEnvVars
      }],
      memory,
      taskPolicies,
      serviceName
    });
  }

  public get pgDatabase(): RdsPostgres {
    return this._pgDatabase;
  }
  public get deploymentPipeline (): DeploymentPipeline {
    return this._deploymentPipeline;
  }
  public get server (): ComputeService {
    return this._server;
  }
}