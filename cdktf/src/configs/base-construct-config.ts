export type BaseConstructConfig = {
  environment: string;
  accountId?: string;
  region?: string;
}

export type DefaultedBaseConstructConfig = BaseConstructConfig & {
  accountId: string;
  region: string;
}