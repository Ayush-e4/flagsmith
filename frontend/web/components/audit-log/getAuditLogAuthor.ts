import { AuditLogItem } from 'common/types/responses'
import getUserDisplayName from 'common/utils/getUserDisplayName'

type AuditLogAuthorItem = Pick<
  AuditLogItem,
  'author' | 'master_api_key' | 'is_system_event'
>

// Who made a change: a user, a Master API key (e.g. Terraform or CI), or
// Flagsmith itself. Never blank, so a missing name reads as a known state.
export const getAuditLogAuthor = (item: AuditLogAuthorItem): string => {
  if (item.author) return getUserDisplayName(item.author)
  if (item.master_api_key) return `${item.master_api_key.name} (API key)`
  if (item.is_system_event) return 'System'
  return getUserDisplayName(undefined)
}
