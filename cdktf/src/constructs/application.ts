import { Construct } from 'constructs';
import {
  cloudwatchLogGroup as cloudwatchLogGroupLib,
  iamRole
} from '@cdktf/provider-aws';

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
      rdsPostgres,
      environmentVariables = [],
      taskPolicies = [],
      memory = 1024
    } = config;

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
            rdsPostgres.secretArn
          ]
        }]
      })
    };
    
    taskPolicies.push(
      pgSecretsManagerAccess
    )
    environmentVariables.push(...[
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