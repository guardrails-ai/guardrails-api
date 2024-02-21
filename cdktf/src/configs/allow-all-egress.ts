import {
  securityGroup as securityGroupLib
} from '@cdktf/provider-aws';

import SecurityGroupEgress =  securityGroupLib.SecurityGroupEgress;

export const ALLOW_ALL_EGRESS: SecurityGroupEgress = {
  fromPort: 0,
  toPort: 0,
  protocol: '-1',
  cidrBlocks: ['0.0.0.0/0'],
  ipv6CidrBlocks: ['::/0']
};