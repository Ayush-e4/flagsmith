import { getAuditLogAuthor } from 'components/audit-log/getAuditLogAuthor'

const user = {
  email: 'kyle@example.com',
  first_name: 'Kyle',
  id: 1,
  last_login: null,
  last_name: 'Johnson',
  uuid: 'user-uuid',
}

const apiKey = { name: 'terraform-prod', prefix: 'wuKWVo1R' }

describe('getAuditLogAuthor', () => {
  it('names the user who made the change', () => {
    expect(
      getAuditLogAuthor({
        author: user,
        is_system_event: false,
        master_api_key: null,
      }),
    ).toBe('Kyle Johnson')
  })

  it('names the Master API key a change was made with', () => {
    expect(
      getAuditLogAuthor({
        author: null,
        is_system_event: false,
        master_api_key: apiKey,
      }),
    ).toBe('terraform-prod (API key)')
  })

  it('labels system events as System', () => {
    expect(
      getAuditLogAuthor({
        author: null,
        is_system_event: true,
        master_api_key: null,
      }),
    ).toBe('System')
  })

  it('falls back to Unknown when nothing identifies the author', () => {
    expect(
      getAuditLogAuthor({
        author: null,
        is_system_event: false,
        master_api_key: null,
      }),
    ).toBe('Unknown')
  })
})
