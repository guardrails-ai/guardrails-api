import { Construct } from 'constructs';
import { TerraformStack } from 'cdktf';
import { GuardrailsValidationServiceSubStack, GuardrailsValidationServiceSubStackConfig } from '..';

export type GuardrailsTelemetryServiceStackConfig = GuardrailsValidationServiceSubStackConfig;

// This is for if we want to do a multi-stack deployment
export class GuardrailsValidationServiceStack extends TerraformStack {
  constructor (scope: Construct, id: string, config: GuardrailsTelemetryServiceStackConfig) {
    super(scope, id);

    new GuardrailsValidationServiceSubStack(this, `${id}-substack`, config);
  }
}