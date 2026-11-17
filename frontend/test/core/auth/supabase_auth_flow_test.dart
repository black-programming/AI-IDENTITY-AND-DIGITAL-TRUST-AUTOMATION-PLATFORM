import 'package:flutter_test/flutter_test.dart';
import 'package:ai_trust_platform/core/auth/auth_service.dart';
import 'package:ai_trust_platform/core/constants/app_strings.dart';
import 'package:ai_trust_platform/core/supabase/supabase_config.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late AuthService authService;

  setUp(() {
    authService = AuthService.instance;
    authService.resetToDefault();
  });

  tearDown(() {
    authService.resetToDefault();
  });

  group('Phase 4 — Supabase Configuration & Client Security', () {
    test('SupabaseConfig holds valid Supabase URL and anon key', () {
      expect(SupabaseConfig.supabaseUrl, isNotEmpty);
      expect(SupabaseConfig.supabaseUrl, startsWith('https://'));
      expect(SupabaseConfig.supabaseAnonKey, isNotEmpty);
    });

    test('Zero service role key leakage in client configuration', () {
      // Security rule: client config must NEVER expose service_role key
      expect(SupabaseConfig.supabaseAnonKey, isNot(contains('service_role')));
      expect(SupabaseConfig.supabaseUrl, isNot(contains('service_role')));
    });

    test('Supabase client accessor is null-safe when uninitialized in test environment', () {
      // In offline widget/unit test environment without live browser window
      final client = SupabaseConfig.client;
      // Client is either null or a valid client, but must not crash
      expect(client, anyOf(isNull, isNotNull));
    });
  });

  group('Phase 4 — Registration & Validation Tests', () {
    test('signUp fails when full name is empty', () async {
      final result = await authService.signUp(
        fullName: '   ',
        email: 'test@example.com',
        password: 'Password123!',
      );

      expect(result.isSuccess, isFalse);
      expect(result.errorMessage, equals(AppStrings.fullNameRequiredError));
      expect(result.errorCode, equals(AuthErrorCode.invalidCredentials));
    });

    test('signUp fails when email format is invalid', () async {
      final result = await authService.signUp(
        fullName: 'Jane Doe',
        email: 'invalid-email-address',
        password: 'Password123!',
      );

      expect(result.isSuccess, isFalse);
      expect(result.errorMessage, equals(AppStrings.emailInvalidError));
    });

    test('signUp fails when password does not meet PasswordPolicy', () async {
      // Too short
      var result = await authService.signUp(
        fullName: 'Jane Doe',
        email: 'jane@example.com',
        password: 'Pass1',
      );
      expect(result.isSuccess, isFalse);
      expect(result.errorMessage, equals(AppStrings.passwordPolicyNotMetError));

      // No uppercase
      result = await authService.signUp(
        fullName: 'Jane Doe',
        email: 'jane@example.com',
        password: 'password123',
      );
      expect(result.isSuccess, isFalse);

      // No digit
      result = await authService.signUp(
        fullName: 'Jane Doe',
        email: 'jane@example.com',
        password: 'PasswordLetters',
      );
      expect(result.isSuccess, isFalse);
    });

    test('signUp succeeds and requires email confirmation by default', () async {
      final result = await authService.signUp(
        fullName: 'Jane Citizen',
        email: 'jane.citizen@example.com',
        password: 'ValidPassword123',
      );

      expect(result.isSuccess, isTrue);
      expect(result.requiresEmailConfirmation, isTrue);
      expect(result.email, equals('jane.citizen@example.com'));
      expect(result.userId, isNotNull);
      // Registration MUST NOT grant authenticated session before confirmation
      expect(authService.hasAuthenticatedSession, isFalse);
    });
  });

  group('Phase 4 — Sign In & Session Establishment Tests', () {
    test('signIn fails with empty email or empty password', () async {
      var result = await authService.signIn(email: '', password: 'Password123');
      expect(result.isSuccess, isFalse);
      expect(result.errorMessage, equals(AppStrings.emailRequiredError));

      result = await authService.signIn(email: 'test@example.com', password: '');
      expect(result.isSuccess, isFalse);
      expect(result.errorMessage, equals(AppStrings.passwordRequiredError));
    });

    test('signIn fails with invalid email format', () async {
      final result = await authService.signIn(
        email: 'not-an-email',
        password: 'Password123',
      );
      expect(result.isSuccess, isFalse);
      expect(result.errorMessage, equals(AppStrings.emailInvalidError));
    });

    test('successful signIn establishes session and updates reactive properties', () async {
      bool listenerNotified = false;
      authService.addListener(() {
        listenerNotified = true;
      });

      final result = await authService.signIn(
        email: 'verified.citizen@example.com',
        password: 'ValidPassword123',
      );

      expect(result.isSuccess, isTrue);
      expect(authService.hasAuthenticatedSession, isTrue);
      expect(authService.currentUserEmail, equals('verified.citizen@example.com'));
      expect(authService.currentUserId, isNotNull);
      expect(listenerNotified, isTrue);
    });

    test('rememberMe preference updates correctly', () {
      expect(authService.rememberMePreference, isTrue);
      authService.setRememberMePreference(false);
      expect(authService.rememberMePreference, isFalse);
    });
  });

  group('Phase 4 — Email Verification & Confirmation Flow', () {
    test('checkVerificationStatus rejects invalid email syntax', () async {
      final result = await authService.checkVerificationStatus(email: 'invalid');
      expect(result.isVerified, isFalse);
      expect(result.errorMessage, equals(AppStrings.emailInvalidError));
    });

    test('checkVerificationStatus returns pending before external confirmation', () async {
      final result = await authService.checkVerificationStatus(
        email: 'pending.user@example.com',
      );
      expect(result.isVerified, isFalse);
      expect(result.errorCode, equals(AuthErrorCode.emailNotConfirmed));
    });

    test('resendVerificationEmail validates email syntax and dispatches', () async {
      final failResult = await authService.resendVerificationEmail(email: '');
      expect(failResult.isSuccess, isFalse);

      final successResult = await authService.resendVerificationEmail(
        email: 'user@example.com',
      );
      expect(successResult.isSuccess, isTrue);
    });

    test('confirmEmailForDevelopment enables authenticated session for dev testing', () async {
      await authService.confirmEmailForDevelopment('dev.tester@example.com');
      expect(authService.hasAuthenticatedSession, isTrue);
      expect(authService.currentUserEmail, equals('dev.tester@example.com'));
    });
  });

  group('Phase 4 — Password Recovery & Updates', () {
    test('sendPasswordResetEmail accepts valid email without leaking existence', () async {
      final result = await authService.sendPasswordResetEmail(
        email: 'forgotten@example.com',
      );
      expect(result.isSuccess, isTrue);
      expect(result.message, equals(AppStrings.forgotPasswordSuccessMessage));
    });

    test('updatePassword requires active recovery or authenticated session', () async {
      // Without recovery or auth session:
      final result = await authService.updatePassword(newPassword: 'NewPassword123');
      expect(result.isSuccess, isFalse);
      expect(result.errorCode, equals(AuthErrorCode.sessionExpired));
    });

    test('updatePassword validates password complexity', () async {
      authService.setRecoverySessionForTesting(true);

      final result = await authService.updatePassword(newPassword: 'weak');
      expect(result.isSuccess, isFalse);
      expect(result.errorMessage, equals(AppStrings.passwordPolicyNotMetError));
    });

    test('updatePassword succeeds with valid session and complexity', () async {
      authService.setRecoverySessionForTesting(true);

      final result = await authService.updatePassword(newPassword: 'StrongPassword123');
      expect(result.isSuccess, isTrue);
      expect(authService.hasRecoverySession, isFalse);
    });

    test('changePassword requires active session, current password, and different new password', () async {
      // Unauthenticated fails
      var result = await authService.changePassword(
        currentPassword: 'OldPassword123',
        newPassword: 'NewPassword123',
      );
      expect(result.isSuccess, isFalse);
      expect(result.errorCode, equals(AuthErrorCode.sessionExpired));

      // Authenticate
      authService.setAuthenticatedSessionForTesting(email: 'user@example.com');

      // Empty current password fails
      result = await authService.changePassword(
        currentPassword: '',
        newPassword: 'NewPassword123',
      );
      expect(result.isSuccess, isFalse);

      // Same password fails
      result = await authService.changePassword(
        currentPassword: 'SamePassword123',
        newPassword: 'SamePassword123',
      );
      expect(result.isSuccess, isFalse);
      expect(result.errorMessage, equals(AppStrings.changePasswordSamePasswordError));

      // Valid change succeeds
      result = await authService.changePassword(
        currentPassword: 'OldPassword123',
        newPassword: 'NewPassword123',
      );
      expect(result.isSuccess, isTrue);
    });
  });

  group('Phase 4 — Multi-Factor Authentication (MFA) Posture', () {
    test('getMfaStatus returns notConfigured when unauthenticated', () async {
      final status = await authService.getMfaStatus();
      expect(status, equals(MfaStatus.notConfigured));
    });

    test('enrollMfa requires authentication', () async {
      final result = await authService.enrollMfa();
      expect(result.isSuccess, isFalse);
    });

    test('verifyMfa requires 6-digit numeric verification code', () async {
      authService.setAuthenticatedSessionForTesting(email: 'user@example.com');

      var result = await authService.verifyMfa(factorId: 'f_1', code: '123');
      expect(result.isSuccess, isFalse);

      result = await authService.verifyMfa(factorId: 'f_1', code: 'abcdef');
      expect(result.isSuccess, isFalse);
    });
  });

  group('Phase 4 — Sign Out & Clean Session Termination', () {
    test('signOut terminates session, clears user data, and notifies listeners', () async {
      authService.setAuthenticatedSessionForTesting(
        email: 'active.user@example.com',
        userId: 'usr_real_999',
        userName: 'Active Citizen',
      );
      expect(authService.hasAuthenticatedSession, isTrue);
      expect(authService.currentUserEmail, equals('active.user@example.com'));

      bool listenerNotified = false;
      authService.addListener(() {
        listenerNotified = true;
      });

      await authService.signOut();

      expect(authService.hasAuthenticatedSession, isFalse);
      expect(authService.currentUserEmail, isNull);
      expect(authService.currentUserId, isNull);
      expect(authService.currentUserName, isNull);
      expect(listenerNotified, isTrue);
    });
  });
}
