# Implementation Plan: Gestão de Status e Assinatura Digital

## Overview

Este plano implementa o sistema completo de gestão de status de funcionários e assinatura digital de Vale-Transporte para o sistema RENAPSI. A implementação será incremental, começando pela infraestrutura de banco de dados, seguindo para o gerenciamento de tokens, depois a interface de assinatura, e finalmente a integração com o sistema existente.

## Tasks

- [ ] 1. Setup database infrastructure and migrations
  - [x] 1.1 Create tokens_assinatura table with indexes
    - Implement `criar_tabela_tokens()` in banco_dados.py
    - Create table with all required columns: id, token, consulta_id, created_at, expires_at, used, used_at
    - Add indexes on token, consulta_id, and expires_at for performance
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9_
  
  - [x] 1.2 Add signature columns to jovens_rotas table
    - Implement `adicionar_colunas_assinatura()` in banco_dados.py
    - Add columns: assinatura_path, assinatura_data, assinatura_ip
    - Handle gracefully if columns already exist (try/except OperationalError)
    - _Requirements: 9.1, 9.2, 9.3, 9.7_
  
  - [x] 1.3 Create database initialization function
    - Implement `inicializar_banco_completo()` in banco_dados.py
    - Call existing functions plus new table/column creation functions
    - Ensure idempotent execution (safe to run multiple times)
    - _Requirements: 8.9, 9.7_

- [ ] 2. Implement token management module (token_manager.py)
  - [x] 2.1 Create token_manager.py with token generation function
    - Implement `gerar_token(consulta_id: int) -> dict`
    - Use secrets.token_urlsafe(32) for cryptographic security
    - Calculate created_at and expires_at (30 days)
    - Store token in database with retry logic for collisions (max 3 attempts)
    - Return dict with token, url, created_at, expires_at
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7, 2.8_
  
  - [ ]* 2.2 Write property test for token uniqueness
    - **Property 4: Token Uniqueness**
    - **Validates: Requirements 2.7**
    - Generate multiple tokens for same consulta_id and verify all are unique
  
  - [ ]* 2.3 Write property test for token security requirements
    - **Property 5: Token Security Requirements**
    - **Validates: Requirements 2.2**
    - Verify all generated tokens are >= 32 characters
  
  - [ ]* 2.4 Write property test for token expiration calculation
    - **Property 6: Token Expiration Calculation**
    - **Validates: Requirements 2.4**
    - Verify expires_at is exactly 30 days after created_at
  
  - [x] 2.5 Implement token validation function
    - Implement `validar_token(token: str) -> dict`
    - Validate token format (alphanumeric, correct length)
    - Check if token exists in database
    - Check if token is expired (current_time > expires_at)
    - Check if token is already used (used = 1)
    - Load and return consulta data if valid
    - Return error codes: 'invalido', 'expirado', 'usado'
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  
  - [ ]* 2.6 Write property test for valid token retrieves consulta
    - **Property 11: Valid Token Retrieves Consulta**
    - **Validates: Requirements 3.5, 3.6**
    - Verify valid tokens successfully retrieve consulta data
  
  - [ ]* 2.7 Write property test for invalid token shows error
    - **Property 12: Invalid Token Shows Error**
    - **Validates: Requirements 3.2, 3.3, 3.4**
    - Verify invalid/expired/used tokens return appropriate errors
  
  - [x] 2.8 Implement token usage marking function
    - Implement `marcar_token_usado(token: str) -> bool`
    - Set used = 1 and record used_at timestamp
    - Return True on success, False on failure
    - _Requirements: 12.1, 12.2_
  
  - [ ]* 2.9 Write property test for used token rejection
    - **Property 21: Used Token Rejection**
    - **Validates: Requirements 12.3**
    - Verify tokens marked as used cannot be validated again
  
  - [x] 2.10 Implement token cleanup function
    - Implement `limpar_tokens_expirados() -> int`
    - Delete only tokens where used=0 AND expires_at < current_timestamp
    - Preserve all used tokens regardless of expiration (audit trail)
    - Return count of deleted tokens
    - Add logging for cleanup operations
    - _Requirements: 15.1, 15.4, 15.5, 15.7_
  
  - [ ]* 2.11 Write property test for token cleanup selectivity
    - **Property 22: Token Cleanup Selectivity**
    - **Validates: Requirements 15.4, 15.5**
    - Verify cleanup only removes expired unused tokens, preserves used tokens

- [x] 3. Checkpoint - Ensure token management tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Extend banco_dados.py with signature-related functions
  - [x] 4.1 Implement function to update consulta with signature
    - Implement `atualizar_consulta_com_assinatura(consulta_id, filepath, ip_address) -> bool`
    - Update status_rota to 'Implantado'
    - Store assinatura_path, assinatura_data, assinatura_ip
    - Use transaction for atomicity
    - _Requirements: 6.9, 9.4, 9.5, 9.6_
  
  - [ ]* 4.2 Write property test for assinatura atomicity
    - **Property 16: Assinatura Atomicity**
    - **Validates: Requirements 6.8, 6.9, 6.10, 7.4**
    - Verify all 4 operations occur together: save file, update status, store path, mark token used
  
  - [x] 4.3 Implement helper functions for status management
    - Implement `obter_status_consulta(consulta_id: int) -> str`
    - Implement `verificar_token_usado(token: str) -> bool`
    - These support testing and UI logic
    - _Requirements: 1.8_

- [ ] 5. Create signature page (assinatura_digital.py)
  - [ ] 5.1 Create assinatura_digital.py with main page structure
    - Implement `main()` function with page config
    - Extract token from st.query_params
    - Handle missing token case with error message
    - Apply dark theme CSS consistent with main app
    - _Requirements: 4.1, 4.10, 10.1, 10.2, 10.3_
  
  - [ ] 5.2 Implement token validation and error handling
    - Call validar_token() and handle all error cases
    - Display appropriate error messages for: invalid, expired, used tokens
    - Implement `exibir_erro_token(erro: str)` function
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.7, 10.5_
  
  - [ ] 5.3 Implement information display functions
    - Implement `exibir_header()` - logo and title
    - Implement `exibir_cards_informacao(dados)` - consulta ID, cost, distance, time
    - Use st.columns for responsive card layout
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ] 5.4 Implement route visualization
    - Implement `exibir_mapa_rota(dados)` using Folium
    - Implement `exibir_detalhes_rota(dados)` - modal, trajectory, lines
    - Display complete route from home to work
    - _Requirements: 4.6, 4.7, 4.8, 4.9_
  
  - [ ] 5.5 Implement action buttons
    - Create "Baixar Carta" button with PDF download
    - Create "Cancelar VT (Não Optante)" button
    - Create "Aceitar e Assinar" button
    - Implement `baixar_carta_pdf(dados)` function
    - _Requirements: 5.1, 5.3, 5.7, 5.9_
  
  - [ ]* 5.6 Write property test for download preserves status
    - **Property 13: Download Preserves Status**
    - **Validates: Requirements 5.2**
    - Verify downloading carta does not change status_rota
  
  - [ ] 5.7 Implement cancelamento (Não Optante) logic
    - Implement `processar_cancelamento(consulta_id, token)` function
    - Update status_rota to "Não Optante"
    - Mark token as used atomically
    - Display confirmation message
    - _Requirements: 5.4, 5.5, 5.6_
  
  - [ ]* 5.8 Write property test for cancelamento atomicity
    - **Property 14: Cancelamento Atomicity**
    - **Validates: Requirements 5.4, 5.5**
    - Verify status update and token marking happen together

- [ ] 6. Implement signature capture modal
  - [ ] 6.1 Create signature modal with canvas
    - Implement `exibir_modal_assinatura(dados, token)` function
    - Use streamlit-drawable-canvas for signature capture
    - Configure canvas: 600x200px, stroke color #00D4FF, background #0D1117
    - Support both touch and mouse input
    - _Requirements: 6.1, 6.2, 6.3_
  
  - [ ] 6.2 Implement canvas validation and clearing
    - Implement "Limpar" button to reset canvas
    - Implement `canvas_tem_conteudo(image_data)` validation function
    - Check if canvas is empty before allowing confirmation
    - Display error if canvas is empty
    - _Requirements: 6.5, 6.6_
  
  - [ ]* 6.3 Write property test for empty canvas rejection
    - **Property 15: Empty Canvas Rejection**
    - **Validates: Requirements 6.6**
    - Verify empty canvas displays error and prevents confirmation
  
  - [ ] 6.4 Implement signature processing and file saving
    - Implement `processar_assinatura(canvas_result, dados, token)` function
    - Validate canvas has content
    - Generate filename: "assinatura_{consulta_id}_{timestamp}.png"
    - Save PNG to "assinaturas/" directory
    - Verify file was saved successfully before proceeding
    - _Requirements: 6.7, 6.8, 7.1, 7.2, 7.3, 7.6_
  
  - [ ]* 6.5 Write property test for signature file naming convention
    - **Property 17: Signature File Naming Convention**
    - **Validates: Requirements 7.1, 7.2, 7.3**
    - Verify filenames match pattern and are stored in correct directory
  
  - [ ] 6.6 Implement atomic database update for signature
    - Use database transaction in processar_assinatura
    - Update jovens_rotas with status, path, timestamp, IP
    - Mark token as used
    - Rollback and delete file if transaction fails
    - Display success message with balloons animation
    - _Requirements: 6.9, 6.10, 6.11, 7.4, 7.7_
  
  - [ ]* 6.7 Write property test for file save before status update
    - **Property 18: File Save Before Status Update**
    - **Validates: Requirements 7.6, 7.7**
    - Verify status is not updated if file save fails
  
  - [ ] 6.8 Implement visual feedback and loading states
    - Add loading spinner during signature processing
    - Display success message after confirmation
    - Disable buttons during processing to prevent double submission
    - Implement `obter_ip_cliente()` helper function
    - _Requirements: 6.12, 13.2, 13.3, 13.7_

- [ ] 7. Checkpoint - Ensure signature page tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Integrate with email system
  - [ ] 8.1 Extend email_sender.py with token URL support
    - Modify `enviar_carta_por_email()` or create new `enviar_carta_com_token()` function
    - Add token_url parameter
    - Update email HTML template to include signature link section
    - Add clear instructions: "Para assinar digitalmente sua carta de VT, acesse: {URL}"
    - Include note about 30-day validity and single use
    - _Requirements: 2.6, 11.2, 11.3, 11.4_
  
  - [ ]* 8.2 Write property test for email contains token URL
    - **Property 9: Email Contains Token URL**
    - **Validates: Requirements 2.6, 11.3**
    - Verify email body contains the generated token URL
  
  - [ ]* 8.3 Write property test for token generation before email
    - **Property 19: Token Generation Before Email**
    - **Validates: Requirements 11.1, 11.5**
    - Verify token is stored in database before email is sent

- [ ] 9. Integrate with main application (app_piloto.py)
  - [ ] 9.1 Add routing logic for signature page
    - Modify `main()` function to detect 'token' query parameter
    - Import and call assinatura_digital.main() when token is present
    - Return early to prevent rendering main menu
    - _Requirements: 10.1, 10.2, 10.4, 10.6, 10.7_
  
  - [ ] 9.2 Update email sending workflow with token generation
    - In email modal, call gerar_token() before sending email
    - Pass token URL to email sending function
    - Display generated URL in success message for admin reference
    - Handle token generation errors gracefully
    - _Requirements: 2.1, 11.1, 11.5, 11.6_
  
  - [ ] 9.3 Implement status-based UI controls
    - Disable "Recalcular Rota" button when status is "Implantado" or "Não Optante"
    - Disable "Enviar Carta" button when status is "Implantado" or "Não Optante"
    - Display visual warning when route is already deployed
    - Add color coding for status display (green=Implantado, red=Não Optante, blue=Otimizado)
    - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 13.6_
  
  - [ ]* 9.4 Write property test for status value constraint
    - **Property 1: Status Value Constraint**
    - **Validates: Requirements 1.1**
    - Verify status_rota only contains valid values: "Otimizado", "Implantado", "Não Optante"
  
  - [ ]* 9.5 Write property test for default status initialization
    - **Property 2: Default Status Initialization**
    - **Validates: Requirements 1.2**
    - Verify new consultas are initialized with status "Otimizado"
  
  - [ ]* 9.6 Write property test for UI control based on status
    - **Property 3: UI Control Based on Status**
    - **Validates: Requirements 1.3, 1.4, 1.6, 1.7**
    - Verify route recalculation and carta sending are disabled for "Implantado" and "Não Optante"
  
  - [ ] 9.7 Add database initialization to application startup
    - Call `inicializar_banco_completo()` at the start of main()
    - Ensure tables and columns are created before any operations
    - _Requirements: 8.9, 9.7_
  
  - [ ] 9.8 Add token cleanup to application startup
    - Call `limpar_tokens_expirados()` at startup
    - Log cleanup results
    - _Requirements: 15.2, 15.3_
  
  - [ ]* 9.9 Write property test for cleanup execution on startup
    - **Property 23: Cleanup Execution on Startup**
    - **Validates: Requirements 15.2**
    - Verify cleanup function is called during application initialization

- [ ] 10. Implement responsive design and mobile support
  - [ ] 10.1 Add responsive CSS for mobile devices
    - Stack information cards vertically on screens < 768px
    - Make map responsive with proper aspect ratio
    - Ensure buttons are touch-friendly (minimum 44x44 pixels)
    - Set minimum font size to 14px for readability
    - Make modal full-screen on mobile devices
    - _Requirements: 14.1, 14.2, 14.3, 14.5, 14.6, 14.7_
  
  - [ ] 10.2 Optimize canvas for touch devices
    - Configure streamlit-drawable-canvas for touch input
    - Detect device type and adjust canvas settings
    - Test touch gestures work correctly
    - _Requirements: 14.4, 14.8_

- [ ] 11. Implement security features
  - [ ] 11.1 Add input validation and sanitization
    - Validate token format before database lookup
    - Prevent directory traversal in file paths
    - Validate file extensions (.png only)
    - _Requirements: 12.5_
  
  - [ ] 11.2 Implement audit logging
    - Log all token validation attempts (success and failure)
    - Log token generation events
    - Log signature confirmations with IP and timestamp
    - Log cleanup operations
    - _Requirements: 12.6, 15.3_
  
  - [ ] 11.3 Add rate limiting for token validation
    - Implement rate limiting: max 10 attempts per IP per hour
    - Display error message when limit exceeded
    - Log potential brute force attempts
    - _Requirements: 12.7_
  
  - [ ] 11.4 Set file permissions for signature directory
    - Ensure assinaturas/ directory has correct permissions
    - Verify files are readable only by authorized processes
    - _Requirements: 7.5_

- [ ] 12. Add visual feedback and UX improvements
  - [ ] 12.1 Implement loading states
    - Add spinner when page is loading
    - Add spinner during signature processing
    - Add spinner during email sending
    - _Requirements: 13.1, 13.2_
  
  - [ ] 12.2 Implement success and error messages
    - Display success message with checkmark for signature confirmation
    - Display confirmation message for VT cancellation
    - Display clear error messages for all error cases
    - Use consistent color coding (green=success, red=error, blue=info)
    - _Requirements: 13.3, 13.4, 13.5, 13.6_
  
  - [ ] 12.3 Implement button state management
    - Disable buttons after click to prevent double submission
    - Re-enable or redirect after action completes
    - _Requirements: 13.7, 13.8_

- [ ] 13. Create assinaturas directory and update dependencies
  - [ ] 13.1 Create assinaturas directory with .gitkeep
    - Create directory structure
    - Add .gitkeep file to track empty directory in git
    - Ensure directory is writable by application
  
  - [ ] 13.2 Update requirements.txt
    - Add streamlit-drawable-canvas==0.9.3
    - Add hypothesis==6.88.0 for property-based testing
    - Add pytest==7.4.2 for unit testing
    - Verify all other dependencies are up to date
  
  - [ ] 13.3 Update .env with new configuration
    - Add BASE_URL (default: http://localhost:8501)
    - Add TOKEN_EXPIRATION_DAYS (default: 30)
    - Add ASSINATURAS_DIR (default: assinaturas)
    - Add ENABLE_RATE_LIMITING (default: true)
    - Add MAX_ATTEMPTS_PER_HOUR (default: 10)

- [ ] 14. Final checkpoint - Integration testing
  - [ ]* 14.1 Write integration test for complete signature flow
    - Test end-to-end: create consulta → generate token → send email → validate token → sign → verify final state
    - Verify all database updates are correct
    - Verify signature file is saved
    - Verify token cannot be reused
  
  - [ ]* 14.2 Write integration test for complete cancelamento flow
    - Test end-to-end: create consulta → generate token → cancel VT → verify final state
    - Verify status is "Não Optante"
    - Verify token is marked as used
  
  - [ ]* 14.3 Write integration test for token cleanup
    - Create tokens in various states (expired/valid, used/unused)
    - Run cleanup
    - Verify only expired unused tokens are removed
  
  - [ ] 14.4 Manual testing checklist
    - Test on Chrome, Firefox, Safari (desktop)
    - Test on Chrome mobile, Safari mobile
    - Test complete user flows
    - Test error scenarios (invalid token, expired token, used token)
    - Test security features (rate limiting)
    - Verify responsive design on various screen sizes
  
  - [ ] 14.5 Final verification
    - Ensure all tests pass
    - Verify code coverage meets 85% threshold
    - Run linter (flake8, black) and fix issues
    - Review all error handling paths
    - Ask the user if questions arise before deployment

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Integration tests verify end-to-end flows work correctly
- The implementation follows a bottom-up approach: database → business logic → UI → integration
- All database operations use transactions for atomicity
- Security is built-in from the start (token security, rate limiting, audit logging)
- The design is mobile-first and responsive
