import { Construct } from 'constructs';
import { Apigatewayv2VpcLink } from '@cdktf/provider-aws/lib/apigatewayv2-vpc-link';
import { Apigatewayv2Api } from '@cdktf/provider-aws/lib/apigatewayv2-api';
import { Apigatewayv2Integration } from '@cdktf/provider-aws/lib/apigatewayv2-integration';
import { ServiceDiscoveryPrivateDnsNamespace } from '@cdktf/provider-aws/lib/service-discovery-private-dns-namespace';
import { ServiceDiscoveryService } from '@cdktf/provider-aws/lib/service-discovery-service';
import { Apigatewayv2Route } from '@cdktf/provider-aws/lib/apigatewayv2-route';
import { TerraformOutput } from 'cdktf';
import { Apigatewayv2Stage } from '@cdktf/provider-aws/lib/apigatewayv2-stage';
import { BaseConstructConfig } from '../../../../src/configs';

export type GatewayConfig = BaseConstructConfig & {
  serviceName: string;
  vpcLink: Apigatewayv2VpcLink;
  serviceDiscoveryNamespace: ServiceDiscoveryPrivateDnsNamespace;
};

export class Gateway extends Construct {
  private _api: Apigatewayv2Api;
  private _discoveryService: ServiceDiscoveryService;
  private _integration: Apigatewayv2Integration;
  private _route: Apigatewayv2Route;
  private _stage: Apigatewayv2Stage;

  constructor (scope: Construct, id: string, config: GatewayConfig) {
    super(scope, id);

    const {
      serviceName,
      vpcLink,
      serviceDiscoveryNamespace
    } = config;

    this._api = new Apigatewayv2Api(this, `${id}-http-api`, {
      name: `${serviceName}-gateway`,
      description: 'Integration between apigw and Fargate Service',
      protocolType: 'HTTP'
    });

    this._discoveryService = new ServiceDiscoveryService(this, `${id}-service-discovery-service`, {
      name: `${serviceName}-discovery-service`,
      dnsConfig: {
        namespaceId: serviceDiscoveryNamespace.id,
        dnsRecords: [
          {
            ttl: 10,
            type: 'SRV'
          }
        ],
        routingPolicy: 'MULTIVALUE'
      }
    });

    this._integration = new Apigatewayv2Integration(this, `${id}-api-integration`, {
      apiId: this._api.id,
      connectionId: vpcLink.id,
      connectionType: 'VPC_LINK',
      description: 'API Integration with AWS Fargate Service',
      integrationMethod: 'ANY', // for GET and POST, use ANY
      integrationType: 'HTTP_PROXY',
      integrationUri: this._discoveryService.arn,
      payloadFormatVersion: '1.0' // supported values for Lambda proxy integrations are 1.0 and 2.0. For all other integrations, 1.0 is the only supported value
    });

    this._route = new Apigatewayv2Route(this, `${id}-route`, {
      apiId: this._api.id,
      routeKey: 'ANY /{proxy+}',
      target: `integrations/${this._integration.id}`
    });

    this._stage = new Apigatewayv2Stage(this, `${id}-default-stage`, {
      apiId: this._api.id,
      name: '$default',
      autoDeploy: true
    });

    new TerraformOutput(this, `${id}-apig-url`, {
      value: this._api.apiEndpoint,
      description: 'API Gateway URL to access the endpoint'
    });
  }

  public get api (): Apigatewayv2Api {
    return this._api;
  }
  public get discoveryService (): ServiceDiscoveryService {
    return this._discoveryService;
  }
  public get integration (): Apigatewayv2Integration {
    return this._integration;
  }
  public get route (): Apigatewayv2Route {
    return this._route;
  }
  public get stage (): Apigatewayv2Stage {
    return this._stage;
  }
}