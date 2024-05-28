import { Construct } from 'constructs';
import { CloudwatchLogGroup } from '@cdktf/provider-aws/lib/cloudwatch-log-group';
import { EcsService } from '@cdktf/provider-aws/lib/ecs-service';
import { EcsCluster } from '@cdktf/provider-aws/lib/ecs-cluster';
import { Vpc } from '@cdktf/provider-aws/lib/vpc';
import { Subnet } from '@cdktf/provider-aws/lib/subnet';
import { SecurityGroup } from '@cdktf/provider-aws/lib/security-group';
import { Apigatewayv2VpcLink } from '@cdktf/provider-aws/lib/apigatewayv2-vpc-link';
import { ServiceDiscoveryPrivateDnsNamespace } from '@cdktf/provider-aws/lib/service-discovery-private-dns-namespace';
import { Gateway } from './gateway';
import { Task, TaskConfig as TaskConfigRequired } from './task';

export type TaskConfig = Omit<TaskConfigRequired, 'logGroup'>

export type ComputeServiceConfig = TaskConfig & {
  cluster: EcsCluster;
  subnets: Subnet[];
  vpc: Vpc;
  vpcLink: Apigatewayv2VpcLink;
  serviceDiscoveryNamespace: ServiceDiscoveryPrivateDnsNamespace;
  taskCount?: number;
};


export class ComputeService extends Construct {
  private _gateway: Gateway;
  private _logGroup: CloudwatchLogGroup;
  private _securityGroup: SecurityGroup;
  private _service: EcsService;
  private _task: Task;

  constructor (scope: Construct, id: string, config: ComputeServiceConfig) {
    super(scope, id);

    const {
      containers,
      cluster,
      environment,
      serviceName,
      subnets,
      vpc,
      vpcLink,
      serviceDiscoveryNamespace,
      taskCount = 0,
      profile
    } = config;

    this._logGroup = new CloudwatchLogGroup(this, `${id}-logs`, {
      name: `/${serviceName}/${environment}`,
      retentionInDays: 180
    });

    this._securityGroup = new SecurityGroup(this, `${id}-security-group`, {
      vpcId: vpc.id,
      ingress: [
        // only allow incoming traffic from our VPC
        {
          protocol: 'TCP',
          fromPort: containers.at(0)?.port,
          toPort: containers.at(0)?.port,
          securityGroups: [vpc.defaultSecurityGroupId]
        }
      ],
      egress: [
        // allow all outgoing traffic
        {
          fromPort: 0,
          toPort: 0,
          protocol: '-1',
          cidrBlocks: ['0.0.0.0/0'],
          ipv6CidrBlocks: ['::/0']
        }
      ]
    }
    );

    this._gateway = new Gateway(this, `${id}-gateway`, {
      profile,
      environment,
      serviceDiscoveryNamespace,
      serviceName,
      vpcLink
    });

    const taskConfig = { ...config };
    taskConfig.containers.forEach((container) => {
      container.environmentVariables?.push({
        name: 'SELF_ENDPOINT',
        value: this.gateway.api.apiEndpoint
      });
    });

    this._task = new Task(this, `${id}-task`, {
      ...config,
      logGroup: this._logGroup
    });

    this._service = new EcsService(this, `${id}-ecs-service`, {
      name: serviceName,
      taskDefinition: this._task.taskDefinition.arn,
      launchType: 'FARGATE',
      cluster: cluster.arn,
      desiredCount: taskCount,
      networkConfiguration: {
        subnets: subnets.map(s => s.id),
        securityGroups: [vpc.defaultSecurityGroupId, this.securityGroup.id],
        assignPublicIp: false
      },
      enableExecuteCommand: true,
      serviceRegistries: {
        registryArn: this._gateway.discoveryService.arn,
        containerName: containers.at(0)?.name,
        containerPort: containers.at(0)?.port
      }
    });
  }

  public get gateway (): Gateway {
    return this._gateway;
  }
  public get logGroup (): CloudwatchLogGroup {
    return this._logGroup;
  }
  public get securityGroup (): SecurityGroup {
    return this._securityGroup;
  }
  public get service (): EcsService {
    return this._service;
  }
  public get task (): Task {
    return this._task;
  }
}