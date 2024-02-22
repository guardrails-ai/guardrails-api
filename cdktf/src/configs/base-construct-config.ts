export type BaseConstructConfig = {
  environment: string;
  profile: string;
  accountId?: string;
  region?: string;
}

export type DefaultedBaseConstructConfig = BaseConstructConfig & {
  accountId: string;
  region: string;
}