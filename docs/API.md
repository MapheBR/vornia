# API Vornia (OpenAPI)

Documentação gerada a partir de `/openapi.json` do FastAPI (`scripts/export-openapi.py`).

**Título:** Vornia API · **Versão:** 0.1.0

## Autenticação

A API usa **cookies HttpOnly** (`token` com `SameSite=Lax`, `refresh_token` com `SameSite=Strict` e `Path=/api/v1/auth`). O navegador envia os cookies automaticamente; o frontend usa `credentials: 'include'`.

## Convenções

- Prefixo: `/api/v1`
- Isolamento por tenant via RLS: toda query define `request.jwt.claims` com o `company_id` do token
- Erros: `400` validação, `401` não autenticado, `403` sem permissão, `404` não encontrado/outro tenant, `409` conflito, `422` schema inválido, `429` limite excedido (com `Retry-After`)

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register |
| `POST` | `/api/v1/auth/login` | Login |
| `GET` | `/api/v1/auth/me` | Me |
| `POST` | `/api/v1/auth/refresh` | Refresh |
| `POST` | `/api/v1/auth/logout` | Logout |
| `POST` | `/api/v1/employees` | Create Employee |
| `GET` | `/api/v1/employees` | List Employees |
| `GET` | `/api/v1/employees/{employee_id}` | Get Employee |
| `PATCH` | `/api/v1/employees/{employee_id}` | Update Employee |
| `DELETE` | `/api/v1/employees/{employee_id}` | Deactivate Employee |
| `GET` | `/api/v1/settings` | List Settings |
| `GET` | `/api/v1/settings/{key}` | Get Setting |
| `PUT` | `/api/v1/settings/{key}` | Upsert Setting |
| `DELETE` | `/api/v1/settings/{key}` | Delete Setting |
| `POST` | `/api/v1/sync/controlid` | Sync Controlid |
| `GET` | `/api/v1/sync/state` | Sync State |
| `POST` | `/api/v1/sync/process` | Process Journeys |
| `POST` | `/api/v1/balances/recalculate` | Recalculate |
| `GET` | `/api/v1/balances` | List Balances |
| `POST` | `/api/v1/holidays` | Create Holiday |
| `GET` | `/api/v1/holidays` | List Holidays |
| `GET` | `/api/v1/dashboard/summary` | Summary |
| `GET` | `/api/v1/dashboard/inconsistencies` | Inconsistencies |
| `GET` | `/api/v1/exports/journeys.xlsx` | Export Xlsx |
| `GET` | `/api/v1/exports/journeys.pdf` | Export Pdf |
| `PATCH` | `/api/v1/raw-punches/{punch_id}` | Edit Punch |
| `GET` | `/api/v1/audit-logs` | List Audit Logs |
| `GET` | `/health` | Health Check |

## Esquemas

```yaml
EmployeeCreate:
  additionalProperties: false
  description: 'Payload de criacao de colaborador.


    Validadores normalizam CPF/PIS para apenas dígitos e rejeitam vazios.'
  properties:
    control_id:
      anyOf:
      - minimum: 1.0
        type: integer
      - type: 'null'
      title: Control Id
    cpf:
      anyOf:
      - maxLength: 20
        type: string
      - type: 'null'
      title: Cpf
    department:
      anyOf:
      - maxLength: 100
        type: string
      - type: 'null'
      title: Department
    hired_at:
      anyOf:
      - format: date
        type: string
      - type: 'null'
      title: Hired At
    is_active:
      default: true
      title: Is Active
      type: boolean
    job_title:
      anyOf:
      - maxLength: 100
        type: string
      - type: 'null'
      title: Job Title
    name:
      maxLength: 200
      minLength: 1
      title: Name
      type: string
    photo_url:
      anyOf:
      - maxLength: 2048
        type: string
      - type: 'null'
      title: Photo Url
    pis:
      anyOf:
      - maxLength: 20
        type: string
      - type: 'null'
      title: Pis
    registration:
      anyOf:
      - maxLength: 50
        type: string
      - type: 'null'
      title: Registration
    work_schedule:
      anyOf:
      - additionalProperties: true
        type: object
      - type: 'null'
      title: Work Schedule
  required:
  - name
  title: EmployeeCreate
  type: object
EmployeeResponse:
  description: Representacao de colaborador.
  properties:
    cpf:
      anyOf:
      - type: string
      - type: 'null'
      title: Cpf
    created_at:
      format: date-time
      title: Created At
      type: string
    department:
      anyOf:
      - type: string
      - type: 'null'
      title: Department
    hired_at:
      anyOf:
      - format: date
        type: string
      - type: 'null'
      title: Hired At
    id:
      title: Id
      type: string
    is_active:
      default: true
      title: Is Active
      type: boolean
    job_title:
      anyOf:
      - type: string
      - type: 'null'
      title: Job Title
    name:
      title: Name
      type: string
    pis:
      anyOf:
      - type: string
      - type: 'null'
      title: Pis
    registration:
      anyOf:
      - type: string
      - type: 'null'
      title: Registration
    updated_at:
      format: date-time
      title: Updated At
      type: string
  required:
  - id
  - name
  - created_at
  - updated_at
  title: EmployeeResponse
  type: object
EmployeeUpdate:
  additionalProperties: false
  description: Payload de atualização parcial; campos omitidos sao mantidos.
  properties:
    control_id:
      anyOf:
      - minimum: 1.0
        type: integer
      - type: 'null'
      title: Control Id
    cpf:
      anyOf:
      - maxLength: 20
        type: string
      - type: 'null'
      title: Cpf
    department:
      anyOf:
      - maxLength: 100
        type: string
      - type: 'null'
      title: Department
    hired_at:
      anyOf:
      - format: date
        type: string
      - type: 'null'
      title: Hired At
    is_active:
      anyOf:
      - type: boolean
      - type: 'null'
      title: Is Active
    job_title:
      anyOf:
      - maxLength: 100
        type: string
      - type: 'null'
      title: Job Title
    name:
      anyOf:
      - maxLength: 200
        minLength: 1
        type: string
      - type: 'null'
      title: Name
    photo_url:
      anyOf:
      - maxLength: 2048
        type: string
      - type: 'null'
      title: Photo Url
    pis:
      anyOf:
      - maxLength: 20
        type: string
      - type: 'null'
      title: Pis
    registration:
      anyOf:
      - maxLength: 50
        type: string
      - type: 'null'
      title: Registration
    work_schedule:
      anyOf:
      - additionalProperties: true
        type: object
      - type: 'null'
      title: Work Schedule
  title: EmployeeUpdate
  type: object
HTTPValidationError:
  properties:
    detail:
      items:
        $ref: '#/components/schemas/ValidationError'
      title: Detail
      type: array
  title: HTTPValidationError
  type: object
LoginRequest:
  properties:
    email:
      format: email
      title: Email
      type: string
    password:
      maxLength: 100
      minLength: 1
      title: Password
      type: string
  required:
  - email
  - password
  title: LoginRequest
  type: object
RegisterRequest:
  properties:
    company_name:
      maxLength: 200
      minLength: 1
      title: Company Name
      type: string
    email:
      format: email
      title: Email
      type: string
    full_name:
      maxLength: 200
      minLength: 1
      title: Full Name
      type: string
    password:
      maxLength: 100
      minLength: 8
      title: Password
      type: string
  required:
  - company_name
  - email
  - password
  - full_name
  title: RegisterRequest
  type: object
UserResponse:
  properties:
    company_id:
      title: Company Id
      type: string
    email:
      title: Email
      type: string
    full_name:
      title: Full Name
      type: string
    id:
      title: Id
      type: string
    role:
      title: Role
      type: string
  required:
  - id
  - email
  - full_name
  - company_id
  - role
  title: UserResponse
  type: object
ValidationError:
  properties:
    ctx:
      title: Context
      type: object
    input:
      title: Input
    loc:
      items:
        anyOf:
        - type: string
        - type: integer
      title: Location
      type: array
    msg:
      title: Message
      type: string
    type:
      title: Error Type
      type: string
  required:
  - loc
  - msg
  - type
  title: ValidationError
  type: object

```
