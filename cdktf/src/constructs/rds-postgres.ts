import {
  dbInstance as dbInstanceLib,
  dbSubnetGroup as dbSubnetGroupLib,
  securityGroup as securityGroupLib,
  subnet,
  vpc as vpcLib
} from '@cdktf/provider-aws';
import { Construct } from "constructs";
import { ALLOW_ALL_EGRESS } from "../configs";

import DbInstance = dbInstanceLib.DbInstance;
import DbSubnetGroup = dbSubnetGroupLib.DbSubnetGroup;
import SecurityGroup = securityGroupLib.SecurityGroup;
import Subnet = subnet.Subnet;
import Vpc = vpcLib.Vpc;

export type RdsPostgresConfig = {
  /**
   * @default 5
   */
  allocatedStorage?: number;
  /**
   * @default false
   */
  allowMajorVersionUpgrade?: boolean;
  /**
   * @default true
   */
  autoMinorVersionUpgrade?: boolean;
  availabilityZone?: string;
  /**
   * Backup retention in days
   * @default 7
   */
  backupRetentionPeriod?: number
  /**
   * Where backups are stored
   * Options - 'region' | 'outposts'
   * @default region
   */
  backupTarget?: string;
  /**
   * Daily time range (in UTC) for backups
   * Must not overlap with maintenanceWindow
   * @default '09:00-09:30' UTC (1:00 AM Pacific)
   */
  backupWindow?: string;
  /**
   * @default 'rds-ca-rsa4096-g1'
   */
  caCertIdentifier?: string;
  /**
   * @default '15.4'
   */
  engineVersion?: string;
  /**
   * @default 'db.t4g'
   */
  instanceClass?: string;
  /**
   * The window to perform maintenance in.
   * Syntax: "ddd:hh24:mi-ddd:hh24:mi".
   * Eg: "Mon:00:00-Mon:03:00".
   * @default 'Sun:10:00-Sun:13:00' UTC (Sundays 2:00 - 5:00 AM Pacific)
   */
  maintenanceWindow?: string;
  /**
   * @default true
   */
  multiAz?: boolean;
  /**
   * Name for the Postgres database
   */
  name: string;
  /**
   * @default 5432
   */
  port?: number;
  /**
   * @default 'gp2'
   */
  storageType?: string;
  /**
   * The private subnets with NAT for the Postgres DB to be created in.
   */
  subnets: Subnet[];
  /**
   * The VPC to launch the Postgres DB in.
   */
  vpc: Vpc;
};

export class RdsPostgres extends Construct {
  private _instance: DbInstance;
  private _secretArn: string;
  private _securityGroup: SecurityGroup;
  private _subnetGroup: DbSubnetGroup;

  constructor (scope: Construct, id: string, rdsPostgresConfig: RdsPostgresConfig) {
    super(scope, id);    

    const {
      allocatedStorage = 5,
      availabilityZone,
      allowMajorVersionUpgrade = false,
      autoMinorVersionUpgrade = true,
      backupRetentionPeriod = 7,
      backupTarget = 'region',
      backupWindow = '09:00-09:30',
      caCertIdentifier = 'rds-ca-rsa4096-g1',
      engineVersion = '15.4',
      name: identifier,
      instanceClass = 'db.t4g',
      maintenanceWindow = 'Sun:10:00-Sun:13:00',
      multiAz,
      port = 5432,
      storageType = 'gp2',
      subnets,
      vpc
    } = rdsPostgresConfig;

    this._subnetGroup = new DbSubnetGroup(this, `${id}-db-subnet-group`, {
      namePrefix: identifier,
      description: `Subnet group for ${identifier}; contains private subnets from ${vpc.id}`,
      subnetIds: subnets.map(s => s.id)
    });

    this._securityGroup = new SecurityGroup(this, `${id}-sg`, {
      name: `${identifier}-sg`,
      description: 'Allow traffic from within the vpc',
      vpcId: vpc.id,
      ingress: [
        {
          description: 'TLS from VPC',
          fromPort: 443,
          toPort: 443,
          protocol: 'tcp',
          cidrBlocks: [vpc.cidrBlock]
        },
        {
          description: 'psql from VPC',
          fromPort: 5432,
          toPort: 5432,
          protocol: 'tcp',
          cidrBlocks: [vpc.cidrBlock]
        }
      ],
      egress: [ALLOW_ALL_EGRESS]
    });

    this._instance = new DbInstance(this, `${id}-db-instance`, {
      allocatedStorage,
      allowMajorVersionUpgrade,
      autoMinorVersionUpgrade,
      availabilityZone,
      backupRetentionPeriod,
      backupTarget,
      backupWindow,
      blueGreenUpdate: {
        enabled: false // note supported for Postgres
      },
      caCertIdentifier,
      copyTagsToSnapshot: true,
      dbName: 'postgres',
      dbSubnetGroupName: this.subnetGroup.name,
      deleteAutomatedBackups: true,
      deletionProtection: false,
      engine: 'postgres',
      engineVersion,
      identifier,
      instanceClass,
      maintenanceWindow,
      manageMasterUserPassword: true,
      multiAz,
      port,
      publiclyAccessible: false,
      skipFinalSnapshot: true,
      storageEncrypted: true,
      storageType,
      vpcSecurityGroupIds: [this.securityGroup.id]
    });

    this._secretArn = this.instance.masterUserSecret.get(0).secretArn;
  }

  public get secretArn(): string {
    return this._secretArn;
  }
  public get instance(): DbInstance {
    return this._instance;
  }
  public get securityGroup(): SecurityGroup {
    return this._securityGroup;
  }
  public get subnetGroup(): DbSubnetGroup {
    return this._subnetGroup;
  }
}