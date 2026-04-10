# Requirements Document

## Introduction

Este documento especifica os requisitos para o sistema de gestão de status de funcionários e assinatura digital de Vale-Transporte (VT) para o sistema RENAPSI de mobilidade urbana. O sistema permitirá que funcionários assinem digitalmente suas cartas de VT através de um link único enviado por email, além de gerenciar diferentes status de adesão ao programa de Vale-Transporte.

## Glossary

- **Sistema_VT**: Sistema de gestão de Vale-Transporte RENAPSI
- **Funcionário**: Aprendiz cadastrado no sistema que pode receber Vale-Transporte
- **Consulta**: Registro no banco de dados contendo informações de rota e VT de um funcionário
- **Token_Assinatura**: Código único e seguro gerado para autenticar uma solicitação de assinatura
- **Carta_VT**: Documento PDF contendo detalhes da rota e valor do Vale-Transporte
- **Status_Otimizado**: Estado inicial onde a rota foi calculada mas ainda não foi implantada
- **Status_Implantado**: Estado onde o funcionário assinou e aceitou o VT
- **Status_Nao_Optante**: Estado onde o funcionário optou por não receber VT
- **Página_Assinatura**: Interface web acessível via link único para visualização e assinatura da carta
- **Modal_Assinatura**: Componente de interface para captura da assinatura digital
- **Canvas_Assinatura**: Área interativa onde o funcionário desenha sua assinatura
- **Banco_Tokens**: Tabela SQLite para armazenar tokens de assinatura e seu estado

## Requirements

### Requirement 1: Gestão de Status do Funcionário

**User Story:** Como administrador do sistema, eu quero gerenciar diferentes status de adesão ao VT dos funcionários, para que eu possa controlar o ciclo de vida da implantação do Vale-Transporte.

#### Acceptance Criteria

1. THE Sistema_VT SHALL support three status values: "Otimizado", "Implantado", and "Não Optante"
2. WHEN a new Consulta is created, THE Sistema_VT SHALL set status_rota to "Otimizado"
3. WHEN status_rota equals "Implantado", THE Sistema_VT SHALL disable the route recalculation button
4. WHEN status_rota equals "Implantado", THE Sistema_VT SHALL disable the send carta button
5. WHEN status_rota equals "Implantado", THE Sistema_VT SHALL display a visual warning indicating the route is already deployed
6. WHEN status_rota equals "Não Optante", THE Sistema_VT SHALL disable route calculation functionality
7. WHEN status_rota equals "Não Optante", THE Sistema_VT SHALL disable carta sending functionality
8. THE Sistema_VT SHALL display the current status_rota value in the consultation details panel with appropriate color coding

### Requirement 2: Geração de Token de Assinatura

**User Story:** Como administrador, eu quero que o sistema gere automaticamente um link único e seguro quando envio uma carta por email, para que o funcionário possa acessar a página de assinatura de forma segura.

#### Acceptance Criteria

1. WHEN a Carta_VT is sent via email, THE Sistema_VT SHALL generate a unique Token_Assinatura
2. THE Token_Assinatura SHALL be at least 32 characters long and cryptographically secure
3. THE Token_Assinatura SHALL be stored in Banco_Tokens with the associated Consulta ID
4. THE Token_Assinatura SHALL have an expiration timestamp of 30 days from creation
5. THE Sistema_VT SHALL generate a URL in the format "http://localhost:8501/assinar?token={Token_Assinatura}"
6. THE Sistema_VT SHALL include the generated URL in the email body sent to the Funcionário
7. FOR ALL generated tokens, THE Sistema_VT SHALL ensure uniqueness across the entire Banco_Tokens table
8. THE Sistema_VT SHALL store token creation timestamp, expiration timestamp, and usage status in Banco_Tokens

### Requirement 3: Validação de Token de Assinatura

**User Story:** Como sistema, eu quero validar tokens de assinatura antes de exibir dados sensíveis, para que apenas usuários autorizados possam acessar a página de assinatura.

#### Acceptance Criteria

1. WHEN a user accesses the Página_Assinatura with a Token_Assinatura, THE Sistema_VT SHALL validate the token exists in Banco_Tokens
2. IF the Token_Assinatura does not exist in Banco_Tokens, THEN THE Sistema_VT SHALL display an error message "Token inválido ou expirado"
3. IF the Token_Assinatura has expired (current time > expiration timestamp), THEN THE Sistema_VT SHALL display an error message "Token expirado"
4. IF the Token_Assinatura has already been used (usage status = "used"), THEN THE Sistema_VT SHALL display an error message "Este link já foi utilizado"
5. WHEN token validation succeeds, THE Sistema_VT SHALL retrieve the associated Consulta ID
6. WHEN token validation succeeds, THE Sistema_VT SHALL load all Consulta data for display
7. THE Sistema_VT SHALL perform token validation before rendering any sensitive Funcionário data

### Requirement 4: Página de Assinatura - Exibição de Informações

**User Story:** Como funcionário, eu quero visualizar todas as informações da minha rota e VT em uma página clara e organizada, para que eu possa tomar uma decisão informada sobre aceitar ou recusar o Vale-Transporte.

#### Acceptance Criteria

1. WHEN the Página_Assinatura loads with a valid token, THE Sistema_VT SHALL display a header with logo and title "Assinatura de Vale-Transporte"
2. THE Página_Assinatura SHALL display an information card showing the Consulta ID number
3. THE Página_Assinatura SHALL display an information card showing the daily total cost (round trip fare)
4. THE Página_Assinatura SHALL display an information card showing the walking distance in meters
5. THE Página_Assinatura SHALL display an information card showing the walking time in minutes
6. THE Página_Assinatura SHALL display a Folium map showing the complete route from home to work
7. THE Página_Assinatura SHALL display route details including selected modal (Bus, Metro, Integration)
8. THE Página_Assinatura SHALL display detailed route trajectory information
9. THE Página_Assinatura SHALL display the transit lines used in the route
10. THE Página_Assinatura SHALL use a dark theme consistent with the main application
11. THE Página_Assinatura SHALL be responsive and mobile-friendly

### Requirement 5: Página de Assinatura - Ações do Funcionário

**User Story:** Como funcionário, eu quero ter opções claras para baixar a carta, recusar o VT ou aceitar e assinar, para que eu possa escolher como proceder com minha solicitação de Vale-Transporte.

#### Acceptance Criteria

1. THE Página_Assinatura SHALL display a "Baixar Carta" button that downloads the Carta_VT PDF
2. WHEN the "Baixar Carta" button is clicked, THE Sistema_VT SHALL generate and download the PDF without changing any status
3. THE Página_Assinatura SHALL display a "Cancelar VT" button labeled as "Não Optante"
4. WHEN the "Cancelar VT" button is clicked, THE Sistema_VT SHALL update status_rota to "Não Optante"
5. WHEN the "Cancelar VT" button is clicked, THE Sistema_VT SHALL mark the Token_Assinatura as used
6. WHEN the "Cancelar VT" button is clicked, THE Sistema_VT SHALL display a confirmation message
7. THE Página_Assinatura SHALL display an "Aceitar e Assinar" button
8. WHEN the "Aceitar e Assinar" button is clicked, THE Sistema_VT SHALL open the Modal_Assinatura
9. THE Sistema_VT SHALL provide visual feedback for all button interactions

### Requirement 6: Modal de Assinatura Digital

**User Story:** Como funcionário, eu quero desenhar minha assinatura em uma área dedicada e confirmar minha aceitação, para que eu possa formalizar digitalmente minha adesão ao Vale-Transporte.

#### Acceptance Criteria

1. WHEN the Modal_Assinatura opens, THE Sistema_VT SHALL display a Canvas_Assinatura for drawing
2. THE Canvas_Assinatura SHALL support touch input for mobile devices
3. THE Canvas_Assinatura SHALL support mouse input for desktop devices
4. THE Modal_Assinatura SHALL display a "Confirmar Assinatura" button
5. THE Modal_Assinatura SHALL display a "Limpar" button to clear the Canvas_Assinatura
6. WHEN the Canvas_Assinatura is empty and "Confirmar Assinatura" is clicked, THE Sistema_VT SHALL display an error message "Por favor, desenhe sua assinatura"
7. WHEN "Confirmar Assinatura" is clicked with a valid signature, THE Sistema_VT SHALL capture the Canvas_Assinatura content as an image
8. WHEN signature is confirmed, THE Sistema_VT SHALL save the signature image to the file system
9. WHEN signature is confirmed, THE Sistema_VT SHALL update status_rota to "Implantado"
10. WHEN signature is confirmed, THE Sistema_VT SHALL mark the Token_Assinatura as used in Banco_Tokens
11. WHEN signature is confirmed, THE Sistema_VT SHALL display a success message "Assinatura confirmada com sucesso!"
12. THE Modal_Assinatura SHALL prevent closing while signature processing is in progress

### Requirement 7: Armazenamento de Assinatura

**User Story:** Como sistema, eu quero armazenar assinaturas digitais de forma segura e associada ao funcionário correto, para que eu possa manter um registro auditável das aceitações de VT.

#### Acceptance Criteria

1. WHEN a signature is captured, THE Sistema_VT SHALL save it as a PNG image file
2. THE Sistema_VT SHALL name signature files using the pattern "assinatura_{consulta_id}_{timestamp}.png"
3. THE Sistema_VT SHALL store signature files in a dedicated directory "assinaturas/"
4. THE Sistema_VT SHALL store the signature file path in the jovens_rotas table
5. THE Sistema_VT SHALL ensure signature files are readable only by authorized system processes
6. WHEN a signature is saved, THE Sistema_VT SHALL verify the file was written successfully before updating status
7. IF signature file save fails, THEN THE Sistema_VT SHALL display an error and not update status_rota

### Requirement 8: Banco de Dados - Tabela de Tokens

**User Story:** Como sistema, eu quero uma estrutura de banco de dados dedicada para gerenciar tokens de assinatura, para que eu possa rastrear e validar solicitações de assinatura de forma eficiente.

#### Acceptance Criteria

1. THE Sistema_VT SHALL create a table named "tokens_assinatura" in the SQLite database
2. THE tokens_assinatura table SHALL have a column "id" as INTEGER PRIMARY KEY AUTOINCREMENT
3. THE tokens_assinatura table SHALL have a column "token" as TEXT UNIQUE NOT NULL
4. THE tokens_assinatura table SHALL have a column "consulta_id" as INTEGER NOT NULL
5. THE tokens_assinatura table SHALL have a column "created_at" as TEXT NOT NULL
6. THE tokens_assinatura table SHALL have a column "expires_at" as TEXT NOT NULL
7. THE tokens_assinatura table SHALL have a column "used" as INTEGER DEFAULT 0 (0=unused, 1=used)
8. THE tokens_assinatura table SHALL have a column "used_at" as TEXT (timestamp when token was used)
9. THE Sistema_VT SHALL create this table automatically on application startup if it does not exist

### Requirement 9: Banco de Dados - Extensão da Tabela jovens_rotas

**User Story:** Como sistema, eu quero armazenar informações de assinatura na tabela de funcionários existente, para que eu possa manter todos os dados relacionados ao funcionário em um único local.

#### Acceptance Criteria

1. THE Sistema_VT SHALL add a column "assinatura_path" as TEXT to the jovens_rotas table
2. THE Sistema_VT SHALL add a column "assinatura_data" as TEXT to the jovens_rotas table
3. THE Sistema_VT SHALL add a column "assinatura_ip" as TEXT to the jovens_rotas table
4. WHEN a signature is confirmed, THE Sistema_VT SHALL update assinatura_path with the file path
5. WHEN a signature is confirmed, THE Sistema_VT SHALL update assinatura_data with the current timestamp
6. WHEN a signature is confirmed, THE Sistema_VT SHALL update assinatura_ip with the client IP address
7. THE Sistema_VT SHALL handle missing columns gracefully by creating them via ALTER TABLE if they do not exist

### Requirement 10: Roteamento Streamlit para Página de Assinatura

**User Story:** Como sistema, eu quero usar query parameters do Streamlit para rotear usuários para a página de assinatura, para que funcionários possam acessar a página diretamente via link no email.

#### Acceptance Criteria

1. WHEN a URL contains query parameter "token", THE Sistema_VT SHALL detect it on page load
2. WHEN token parameter is detected, THE Sistema_VT SHALL render the Página_Assinatura instead of the main menu
3. THE Sistema_VT SHALL extract the token value from st.query_params
4. THE Sistema_VT SHALL pass the token value to the validation function
5. WHEN token validation fails, THE Sistema_VT SHALL display an error page with a link to return to the main system
6. WHEN token validation succeeds, THE Sistema_VT SHALL render the full Página_Assinatura interface
7. THE Sistema_VT SHALL maintain the token parameter in the URL throughout the signature process

### Requirement 11: Integração com Envio de Email

**User Story:** Como sistema, eu quero integrar a geração de tokens com o processo existente de envio de email, para que cada carta enviada automaticamente inclua um link de assinatura.

#### Acceptance Criteria

1. WHEN the "Gerar e Enviar" button is clicked in the email modal, THE Sistema_VT SHALL generate a Token_Assinatura before sending the email
2. THE Sistema_VT SHALL construct the signature URL with the generated token
3. THE Sistema_VT SHALL include the signature URL in the email body with clear instructions
4. THE email body SHALL include text: "Para assinar digitalmente sua carta de VT, acesse: {URL}"
5. THE Sistema_VT SHALL send the email only after successfully storing the token in Banco_Tokens
6. IF token generation fails, THEN THE Sistema_VT SHALL display an error and not send the email
7. THE Sistema_VT SHALL maintain backward compatibility with existing email sending functionality

### Requirement 12: Segurança e Prevenção de Reutilização

**User Story:** Como sistema, eu quero garantir que tokens de assinatura não possam ser reutilizados ou manipulados, para que o processo de assinatura seja seguro e auditável.

#### Acceptance Criteria

1. WHEN a Token_Assinatura is used (signature confirmed or VT cancelled), THE Sistema_VT SHALL set the "used" flag to 1
2. WHEN a Token_Assinatura is used, THE Sistema_VT SHALL record the used_at timestamp
3. IF a used Token_Assinatura is accessed again, THEN THE Sistema_VT SHALL display "Este link já foi utilizado"
4. THE Sistema_VT SHALL use secrets.token_urlsafe() or equivalent for token generation
5. THE Sistema_VT SHALL validate token format before database lookup (alphanumeric, correct length)
6. THE Sistema_VT SHALL log all token validation attempts (success and failure) for audit purposes
7. THE Sistema_VT SHALL implement rate limiting to prevent brute force token guessing (max 10 attempts per IP per hour)

### Requirement 13: Feedback Visual e UX

**User Story:** Como funcionário, eu quero receber feedback visual claro em cada etapa do processo de assinatura, para que eu saiba o que está acontecendo e se minhas ações foram bem-sucedidas.

#### Acceptance Criteria

1. WHEN the Página_Assinatura is loading, THE Sistema_VT SHALL display a loading spinner
2. WHEN signature is being processed, THE Sistema_VT SHALL display a loading indicator with text "Processando assinatura..."
3. WHEN signature is confirmed successfully, THE Sistema_VT SHALL display a success message with a checkmark icon
4. WHEN VT is cancelled, THE Sistema_VT SHALL display a confirmation message "Você optou por não receber Vale-Transporte"
5. WHEN an error occurs, THE Sistema_VT SHALL display a clear error message explaining what went wrong
6. THE Sistema_VT SHALL use color coding consistent with the main application (green for success, red for error, blue for info)
7. THE Sistema_VT SHALL disable action buttons after they are clicked to prevent double submission
8. WHEN an action completes, THE Sistema_VT SHALL re-enable appropriate buttons or redirect the user

### Requirement 14: Responsividade Mobile

**User Story:** Como funcionário acessando via smartphone, eu quero que a página de assinatura funcione perfeitamente em dispositivos móveis, para que eu possa assinar minha carta de qualquer lugar.

#### Acceptance Criteria

1. THE Página_Assinatura SHALL render correctly on screens with width >= 320px
2. THE information cards SHALL stack vertically on mobile devices (width < 768px)
3. THE map SHALL be responsive and maintain aspect ratio on all screen sizes
4. THE Canvas_Assinatura SHALL support touch gestures for drawing on mobile devices
5. THE buttons SHALL be large enough for touch interaction (minimum 44x44 pixels)
6. THE text SHALL be readable without zooming on mobile devices (minimum 14px font size)
7. THE Modal_Assinatura SHALL be full-screen on mobile devices for better signature capture
8. THE Sistema_VT SHALL detect device type and optimize Canvas_Assinatura accordingly

### Requirement 15: Limpeza de Tokens Expirados

**User Story:** Como administrador do sistema, eu quero que tokens expirados sejam automaticamente limpos do banco de dados, para que o sistema não acumule dados desnecessários ao longo do tempo.

#### Acceptance Criteria

1. THE Sistema_VT SHALL provide a function to delete tokens where expires_at < current timestamp
2. THE Sistema_VT SHALL execute token cleanup automatically on application startup
3. THE Sistema_VT SHALL log the number of tokens deleted during cleanup
4. THE Sistema_VT SHALL preserve tokens that are expired but have been used (for audit trail)
5. THE Sistema_VT SHALL only delete tokens where used = 0 AND expires_at < current timestamp
6. THE cleanup function SHALL be callable manually by administrators via a dedicated interface
7. THE Sistema_VT SHALL complete token cleanup within 5 seconds for databases with up to 10,000 tokens
