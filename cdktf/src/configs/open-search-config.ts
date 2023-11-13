import {
  opensearchDomain as opensearchDomainLib,
  secretsmanagerSecret as secretsmanagerSecretLib
} from '@cdktf/provider-aws';

import OpensearchDomain = opensearchDomainLib.OpensearchDomain;
import SecretsmanagerSecret = secretsmanagerSecretLib.SecretsmanagerSecret;

export type OpenSearchConfig = {
  opensearchDomain: OpensearchDomain;
  credentials: SecretsmanagerSecret;
}