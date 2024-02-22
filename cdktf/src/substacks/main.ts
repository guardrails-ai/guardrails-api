import { Construct } from 'constructs';
import {
  dataAwsCallerIdentity,
  dataAwsRegion,
  subnet,
  vpc as vpcLib
} from '@cdktf/provider-aws';
import { BaseConstructConfig, DefaultedBaseConstructConfig, OpenSearchConfig } from '../configs';
import {
  Application,
  ApplicationConfig as ApplicationConfigRequired,
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

export type ApplicationConfig = Omit<
  ApplicationConfigRequired,
  'accountId' |
  'containers' |
  'ecrRepo' |
  'cluster' |
  'subnets' |
  'vpc' |
  'vpcLink' |
  'serviceDiscoveryNamespace' |
  'serviceName' |
  'rdsPostgres' |
  'region'
>

export type GuardrailsValidationServiceSubStackConfig = BaseConstructConfig & ApplicationConfig & {
  deploymentPipelineConfig: DeploymentPipelineConfig;
  ecrRepo: EcrRepository;
  openSearchConfig: OpenSearchConfig;
  rdsPostgresConfig?: RdsPostgresConfig;
  subnets: Subnet[];
  vpc: Vpc;
  cluster: EcsCluster;
  vpcLink: Apigatewayv2VpcLink;
  serviceDiscoveryNamespace: ServiceDiscoveryPrivateDnsNamespace;
  taskCount?: number;
}

export class GuardrailsValidationServiceSubStack extends Construct {
  private _pgDatabase: RdsPostgres;
  private _deploymentPipeline: DeploymentPipeline;
  private _application: Application;

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
      profile
    } = config;
    
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

    const applicationConfig: ApplicationConfigRequired = {
      ...config,
      serviceName,
      rdsPostgres: this._pgDatabase
    };
    this._application = new Application(this, `${id}-app`, applicationConfig);
  }

  public get pgDatabase(): RdsPostgres {
    return this._pgDatabase;
  }
  public get deploymentPipeline (): DeploymentPipeline {
    return this._deploymentPipeline;
  }
  public get application (): Application {
    return this._application;
  }
}