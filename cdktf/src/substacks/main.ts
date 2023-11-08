import { Construct } from 'constructs';
import {
  dataAwsCallerIdentity,
  dataAwsRegion,
  ecrRepository,
  subnet,
  vpc as vpcLib
} from '@cdktf/provider-aws';
import { BaseConstructConfig, DefaultedBaseConstructConfig, OpenSearchConfig } from '../configs';
import {
  Application,
  ApplicationConfig,
  DeploymentPipeline,
  DeploymentPipelineConfig as DeploymentPipelineConfigRequired,
  RdsPostgres,
  RdsPostgresConfig as RdsPostgresConfigRequired
} from '../constructs';
import { truncate } from '../utils';

import AwsCallerIdentity = dataAwsCallerIdentity.DataAwsCallerIdentity;
import AwsRegion = dataAwsRegion.DataAwsRegion
import EcrRepository = ecrRepository.EcrRepository;
import Subnet = subnet.Subnet;
import Vpc = vpcLib.Vpc;

export type RdsPostgresConfig = Omit<RdsPostgresConfigRequired, 'name' | 'subnets' | 'vpc'>
export type DeploymentPipelineConfig = Omit<
  DeploymentPipelineConfigRequired,
  'ecrRepo' |
  'lambdaFunctionName' |
  'subnets' |
  'vpc'
>

export type GuadrailsValidationServiceSubStackConfig = BaseConstructConfig & {
  deploymentPipelineConfig: DeploymentPipelineConfig;
  ecrRepo: EcrRepository;
  openSearchConfig: OpenSearchConfig;
  rdsPostgresConfig?: RdsPostgresConfig;
  subnets: Subnet[];
  vpc: Vpc;
}

export class GuadrailsValidationServiceSubStack extends Construct {
  private _pgDatabase: RdsPostgres;
  private _deploymentPipeline: DeploymentPipeline;
  private _application: Application;

  constructor (scope: Construct, id: string, config: GuadrailsValidationServiceSubStackConfig) {
    super(scope, id);

    const currentIdentity = new AwsCallerIdentity(this, `${id}-aws-identity`);
    const defaultAccount: string = currentIdentity.accountId;
    const currentRegion = new AwsRegion(this, `${id}-aws-region`);
    const defaultRegion: string = currentRegion.name;

    const {
      accountId = defaultAccount,
      deploymentPipelineConfig,
      environment,
      ecrRepo,
      openSearchConfig,
      rdsPostgresConfig = {},
      region = defaultRegion,
      subnets,
      vpc
    } = config;

    const baseConfig: DefaultedBaseConstructConfig = {
      accountId,
      environment,
      region
    };

    const baseName = `${id}-guardrails-validation-service`;
    const lambdaFunctionName = truncate(`${baseName}-api-${environment}`, 59); // Allow 5 characters for appending `-role`
    const dbName = `${baseName}-postgres-db`;

    const deploymentPipelineConfigRequired: DeploymentPipelineConfigRequired = {
      ...deploymentPipelineConfig,
      ecrRepo,
      lambdaFunctionName,
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

    this._pgDatabase = new RdsPostgres(this, `${id}-pg-db`, rdsPostgresConfigRequired)

    const applicationConfig: ApplicationConfig = {
      ecrRepo,
      lambdaFunctionName,
      openSearchConfig,
      rdsPostgres: this._pgDatabase,
      vpc,
      subnets
    };
    this._application = new Application(this, `${id}-app`, baseConfig, applicationConfig);
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