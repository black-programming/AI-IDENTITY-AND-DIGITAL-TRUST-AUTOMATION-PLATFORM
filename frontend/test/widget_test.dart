import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_trust_platform/core/constants/app_strings.dart';
import 'package:ai_trust_platform/core/routing/app_routes.dart';
import 'package:ai_trust_platform/main.dart';
import 'package:ai_trust_platform/screens/onboarding/onboarding_identity_screen.dart';
import 'package:ai_trust_platform/screens/onboarding/widgets/identity_benefit_item.dart';
import 'package:ai_trust_platform/screens/onboarding/widgets/identity_card_shield_visual.dart';
import 'package:ai_trust_platform/screens/onboarding/widgets/onboarding_progress_indicator.dart';
import 'package:ai_trust_platform/screens/onboarding/widgets/security_document_shield_visual.dart';
import 'package:ai_trust_platform/screens/onboarding/widgets/trust_verification_visual.dart';
import 'package:ai_trust_platform/core/localization/language_controller.dart';
import 'package:ai_trust_platform/screens/language_selection/language_selection_screen.dart';
import 'package:ai_trust_platform/screens/language_selection/widgets/language_option_card.dart';
import 'package:ai_trust_platform/screens/onboarding/onboarding_security_screen.dart';
import 'package:ai_trust_platform/screens/onboarding/onboarding_trust_screen.dart';
import 'package:ai_trust_platform/screens/splash/splash_screen.dart';
import 'package:ai_trust_platform/screens/splash/widgets/identity_logo.dart';
import 'package:ai_trust_platform/screens/common/route_placeholder_screen.dart';
import 'package:ai_trust_platform/screens/welcome/welcome_screen.dart';
import 'package:ai_trust_platform/screens/welcome/widgets/digital_identity_card_illustration.dart';
import 'package:ai_trust_platform/core/preferences/location_preferences_controller.dart';
import 'package:ai_trust_platform/core/preferences/user_type_controller.dart';
import 'package:ai_trust_platform/screens/country_region/country_region_screen.dart';
import 'package:ai_trust_platform/screens/country_region/widgets/country_selector_field.dart';
import 'package:ai_trust_platform/screens/country_region/widgets/region_selector_field.dart';
import 'package:ai_trust_platform/screens/country_region/widgets/searchable_country_modal.dart';
import 'package:ai_trust_platform/screens/country_region/widgets/searchable_region_modal.dart';
import 'package:ai_trust_platform/screens/user_type/user_type_selection_screen.dart';
import 'package:ai_trust_platform/screens/user_type/widgets/user_type_card.dart';
import 'package:ai_trust_platform/core/preferences/purpose_selection_controller.dart';
import 'package:ai_trust_platform/screens/purpose_selection/purpose_selection_screen.dart';
import 'package:ai_trust_platform/core/preferences/onboarding_state_controller.dart';
import 'package:ai_trust_platform/screens/onboarding_complete/onboarding_complete_screen.dart';
import 'package:ai_trust_platform/screens/onboarding_complete/widgets/onboarding_success_shield_visual.dart';
import 'package:ai_trust_platform/screens/onboarding_complete/widgets/onboarding_summary_card.dart';
import 'package:flutter/gestures.dart';
import 'package:ai_trust_platform/core/auth/auth_service.dart';
import 'package:ai_trust_platform/screens/create_account/create_account_screen.dart';
import 'package:ai_trust_platform/screens/create_account/widgets/password_requirement_item.dart';
import 'package:ai_trust_platform/screens/email_verification/email_verification_screen.dart';
import 'package:ai_trust_platform/screens/login/login_screen.dart';
import 'package:ai_trust_platform/screens/two_factor/two_factor_screen.dart';
import 'package:ai_trust_platform/screens/forgot_password/forgot_password_screen.dart';
import 'package:ai_trust_platform/screens/reset_password/reset_password_screen.dart';
import 'package:ai_trust_platform/screens/change_password/change_password_screen.dart';
import 'package:ai_trust_platform/screens/security_alerts/security_alerts_screen.dart';
import 'package:ai_trust_platform/screens/active_sessions/active_sessions_screen.dart';
import 'package:ai_trust_platform/screens/account_recovery/account_recovery_screen.dart';
import 'package:ai_trust_platform/screens/dashboard/user_dashboard_screen.dart';
import 'package:ai_trust_platform/screens/profile/user_profile_overview_screen.dart';
import 'package:ai_trust_platform/screens/profile/edit_personal_information_screen.dart';
import 'package:ai_trust_platform/screens/profile/profile_photo_screen.dart';
import 'package:ai_trust_platform/screens/verification_status/verification_status_screen.dart';
import 'package:ai_trust_platform/core/data/country_region_data.dart';

void main() {
  group('Screen 001 — Splash Screen Tests', () {
    testWidgets(
      'Renders splash screen brand elements, logo, and loading status',
      (WidgetTester tester) async {
        final completer = Completer<void>();

        await tester.pumpWidget(
          AiTrustApp(initializeAction: () => completer.future),
        );

        // Settle the entrance animations
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 300));

        // Verify product name
        expect(find.text(AppStrings.appName), findsOneWidget);

        // Verify subtitle
        expect(find.text(AppStrings.appSubtitle), findsOneWidget);

        // Verify loading text
        expect(find.text(AppStrings.initializingSecureEnv), findsOneWidget);

        // Verify identity logo widget
        expect(find.byType(IdentityTrustLogo), findsOneWidget);

        // Verify progress indicator
        expect(find.byType(CircularProgressIndicator), findsOneWidget);

        // Clean up pending completer before tear down
        completer.complete();
        await tester.pumpAndSettle();
      },
    );

    testWidgets('Transitions cleanly to welcome screen after initialization', (
      WidgetTester tester,
    ) async {
      final completer = Completer<void>();

      await tester.pumpWidget(
        MaterialApp(
          routes: {
            '/': (context) =>
                SplashScreen(initializeAction: () => completer.future),
            '/welcome': (context) => const WelcomeScreen(),
          },
        ),
      );

      await tester.pump();

      // Initially on Splash
      expect(find.byType(SplashScreen), findsOneWidget);
      expect(find.byType(WelcomeScreen), findsNothing);

      // Complete initialization
      completer.complete();
      await tester.pump();
      await tester.pumpAndSettle();

      // Navigated to Welcome screen
      expect(find.byType(WelcomeScreen), findsOneWidget);
      expect(find.text(AppStrings.welcomeHeading), findsOneWidget);
    });

    testWidgets(
      'Default startup initialization flow completes and navigates to welcome screen',
      (WidgetTester tester) async {
        await tester.pumpWidget(const AiTrustApp());
        await tester.pump();

        // Initially on splash
        expect(find.byType(SplashScreen), findsOneWidget);

        // Fast forward past the 1400ms security initialization timer
        await tester.pump(const Duration(milliseconds: 1500));
        await tester.pumpAndSettle();

        // Verified transition to welcome screen
        expect(find.byType(WelcomeScreen), findsOneWidget);
        expect(find.text(AppStrings.welcomeHeading), findsOneWidget);
      },
    );

    testWidgets('Displays error state gracefully when initialization fails', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          routes: {
            '/': (context) => SplashScreen(
              initializeAction: () async {
                throw Exception('Network security handshake timeout');
              },
            ),
            '/welcome': (context) => const WelcomeScreen(),
          },
        ),
      );

      await tester.pump();
      await tester.pumpAndSettle();

      // Error message should be displayed, no false success
      expect(find.text('Network security handshake timeout'), findsOneWidget);
      expect(find.text(AppStrings.retryInitialization), findsOneWidget);
      expect(find.byType(WelcomeScreen), findsNothing);
    });

    testWidgets('Renders properly without overflow on multiple screen sizes', (
      WidgetTester tester,
    ) async {
      final screenSizes = [
        const Size(320, 568), // Small mobile (iPhone SE)
        const Size(390, 844), // Standard mobile (iPhone 13/14)
        const Size(768, 1024), // Tablet portrait
        const Size(1024, 768), // Tablet landscape
        const Size(1440, 900), // Desktop
      ];

      for (final size in screenSizes) {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1.0;

        final completer = Completer<void>();
        await tester.pumpWidget(
          AiTrustApp(
            key: UniqueKey(),
            initializeAction: () => completer.future,
          ),
        );
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 200));

        // Verify elements render without assertion errors or overflow
        expect(find.text(AppStrings.appName), findsOneWidget);
        expect(find.text(AppStrings.initializingSecureEnv), findsOneWidget);

        completer.complete();
        await tester.pumpAndSettle();
      }

      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
    });
  });

  group('Screen 002 — Welcome Screen Tests', () {
    testWidgets(
      'Renders all required elements, typography, illustration, and actions',
      (WidgetTester tester) async {
        await tester.pumpWidget(const MaterialApp(home: WelcomeScreen()));

        await tester.pumpAndSettle();

        // Heading
        expect(find.text(AppStrings.welcomeHeading), findsOneWidget);

        // Supporting Text
        expect(find.text(AppStrings.welcomeSupporting), findsOneWidget);

        // Identity Card Illustration
        expect(find.byType(DigitalIdentityCardIllustration), findsOneWidget);

        // Buttons
        expect(find.text(AppStrings.getStarted), findsOneWidget);
        expect(find.text(AppStrings.signIn), findsOneWidget);

        // Privacy Footer
        expect(find.text(AppStrings.privacySecurityFooter), findsOneWidget);
      },
    );

    testWidgets('"Get Started" button navigates to onboarding route', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: const WelcomeScreen(),
          onGenerateRoute: AppRoutes.onGenerateRoute,
        ),
      );

      await tester.pumpAndSettle();

      // Ensure button is visible in viewport before tapping
      final getStartedFinder = find.text(AppStrings.getStarted);
      await tester.ensureVisible(getStartedFinder);
      await tester.tap(getStartedFinder);
      await tester.pumpAndSettle();

      // Verifies navigation to Screen 003 Onboarding Identity screen
      expect(find.byType(OnboardingIdentityScreen), findsOneWidget);
      expect(find.text(AppStrings.onboardingIdentityHeading), findsOneWidget);
    });

    testWidgets('"Sign In" button navigates to sign-in route', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: const WelcomeScreen(),
          onGenerateRoute: AppRoutes.onGenerateRoute,
        ),
      );

      await tester.pumpAndSettle();

      // Ensure button is visible in viewport before tapping
      final signInFinder = find.text(AppStrings.signIn);
      await tester.ensureVisible(signInFinder);
      await tester.tap(signInFinder);
      await tester.pumpAndSettle();

      // Verifies navigation to LoginScreen
      expect(find.byType(LoginScreen), findsOneWidget);
      expect(find.text(AppStrings.loginHeading), findsOneWidget);
    });

    testWidgets(
      'Renders WelcomeScreen without overflow on varied screen sizes',
      (WidgetTester tester) async {
        final screenSizes = [
          const Size(320, 568), // Small mobile (iPhone SE)
          const Size(390, 844), // Standard mobile (iPhone 13/14)
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(key: UniqueKey(), home: const WelcomeScreen()),
          );
          await tester.pumpAndSettle();

          expect(find.text(AppStrings.welcomeHeading), findsOneWidget);
          expect(find.text(AppStrings.getStarted), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );
  });

  group('Screen 003 — Onboarding: Identity Screen Tests', () {
    testWidgets(
      'Renders progress indicator, illustration, heading, description, 3 benefits, and actions',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingIdentityScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        // Top progress indicator showing Step 1 of 3
        expect(find.byType(OnboardingProgressIndicator), findsOneWidget);
        expect(find.text(AppStrings.step1Of3), findsOneWidget);

        // Back navigation button
        expect(find.byTooltip(AppStrings.backTooltip), findsOneWidget);

        // Visual representing digital identity card and shield
        expect(find.byType(IdentityCardShieldVisual), findsOneWidget);
        expect(find.byType(DigitalIdentityCardIllustration), findsOneWidget);

        // Heading and description
        expect(find.text(AppStrings.onboardingIdentityHeading), findsOneWidget);
        expect(
          find.text(AppStrings.onboardingIdentityDescription),
          findsOneWidget,
        );

        // Three short benefit points
        expect(find.byType(IdentityBenefitItem), findsNWidgets(3));
        expect(find.text(AppStrings.onboardingBenefit1), findsOneWidget);
        expect(find.text(AppStrings.onboardingBenefit2), findsOneWidget);
        expect(find.text(AppStrings.onboardingBenefit3), findsOneWidget);

        // Primary and secondary action buttons
        expect(find.text(AppStrings.continueAction), findsOneWidget);
        expect(find.text(AppStrings.skipForNow), findsOneWidget);
      },
    );

    testWidgets('"Continue" button navigates to Screen 004 — Security route', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: const OnboardingIdentityScreen(),
          onGenerateRoute: AppRoutes.onGenerateRoute,
        ),
      );

      await tester.pumpAndSettle();

      final continueFinder = find.text(AppStrings.continueAction);
      await tester.ensureVisible(continueFinder);
      await tester.tap(continueFinder);
      await tester.pumpAndSettle();

      // Verifies navigation to Screen 004 Security screen
      expect(find.byType(OnboardingSecurityScreen), findsOneWidget);
      expect(find.text(AppStrings.onboardingSecurityHeading), findsOneWidget);
    });

    testWidgets('"Skip for now" button navigates to user-entry sign-in route', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: const OnboardingIdentityScreen(),
          onGenerateRoute: AppRoutes.onGenerateRoute,
        ),
      );

      await tester.pumpAndSettle();

      final skipFinder = find.text(AppStrings.skipForNow);
      await tester.ensureVisible(skipFinder);
      await tester.tap(skipFinder);
      await tester.pumpAndSettle();

      // Verifies navigation to sign-in destination (LoginScreen)
      expect(find.byType(LoginScreen), findsOneWidget);
      expect(find.text(AppStrings.loginHeading), findsOneWidget);
    });

    testWidgets(
      'Back button navigates back to Welcome screen when opened from Welcome',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const WelcomeScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        // Tap Get Started on Welcome Screen
        final getStartedFinder = find.text(AppStrings.getStarted);
        await tester.ensureVisible(getStartedFinder);
        await tester.tap(getStartedFinder);
        await tester.pumpAndSettle();

        // Verifies we are on Screen 003
        expect(find.byType(OnboardingIdentityScreen), findsOneWidget);

        // Tap Back button
        final backButtonFinder = find.byTooltip(AppStrings.backTooltip);
        expect(backButtonFinder, findsOneWidget);
        await tester.tap(backButtonFinder);
        await tester.pumpAndSettle();

        // Verifies we are back on Welcome screen
        expect(find.byType(WelcomeScreen), findsOneWidget);
        expect(find.text(AppStrings.welcomeHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Back button replaces route to Welcome screen when opened standalone',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingIdentityScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        final backButtonFinder = find.byTooltip(AppStrings.backTooltip);
        expect(backButtonFinder, findsOneWidget);
        await tester.tap(backButtonFinder);
        await tester.pumpAndSettle();

        // Navigated to WelcomeScreen fallback
        expect(find.byType(WelcomeScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Renders OnboardingIdentityScreen without overflow on varied screen sizes',
      (WidgetTester tester) async {
        final screenSizes = [
          const Size(320, 568), // Small mobile (iPhone SE)
          const Size(390, 844), // Standard mobile (iPhone 13/14)
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const OnboardingIdentityScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(
            find.text(AppStrings.onboardingIdentityHeading),
            findsOneWidget,
          );
          expect(find.text(AppStrings.continueAction), findsOneWidget);
          expect(find.text(AppStrings.step1Of3), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets('Action buttons support keyboard navigation and focus', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: const OnboardingIdentityScreen(),
          onGenerateRoute: AppRoutes.onGenerateRoute,
        ),
      );

      await tester.pumpAndSettle();

      // Press Tab key repeatedly to test traversal
      await tester.sendKeyEvent(LogicalKeyboardKey.tab);
      await tester.pumpAndSettle();

      // Verify widget remains stable and interactive
      expect(find.byType(OnboardingIdentityScreen), findsOneWidget);
    });
  });

  group('Screen 004 — Onboarding: Security Screen Tests', () {
    testWidgets(
      'Renders progress indicator, illustration, heading, description, 3 features, and actions',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingSecurityScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        // Top progress indicator showing Step 2 of 3
        expect(find.byType(OnboardingProgressIndicator), findsOneWidget);
        expect(find.text(AppStrings.step2Of3), findsOneWidget);

        // Back navigation button
        expect(find.byTooltip(AppStrings.backTooltip), findsOneWidget);

        // Visual representing shield, lock, and protected digital document
        expect(find.byType(SecurityDocumentShieldVisual), findsOneWidget);

        // Heading and description
        expect(find.text(AppStrings.onboardingSecurityHeading), findsOneWidget);
        expect(
          find.text(AppStrings.onboardingSecurityDescription),
          findsOneWidget,
        );

        // Three short feature points
        expect(find.byType(IdentityBenefitItem), findsNWidgets(3));
        expect(
          find.text(AppStrings.onboardingSecurityFeature1),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.onboardingSecurityFeature2),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.onboardingSecurityFeature3),
          findsOneWidget,
        );

        // Primary and secondary action buttons
        expect(find.text(AppStrings.continueAction), findsOneWidget);
        expect(find.text(AppStrings.backAction), findsOneWidget);
        expect(find.text(AppStrings.skipForNow), findsOneWidget);
      },
    );

    testWidgets('"Continue" button navigates to Screen 005 — Trust route', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: const OnboardingSecurityScreen(),
          onGenerateRoute: AppRoutes.onGenerateRoute,
        ),
      );

      await tester.pumpAndSettle();

      final continueFinder = find.text(AppStrings.continueAction);
      await tester.ensureVisible(continueFinder);
      await tester.tap(continueFinder);
      await tester.pumpAndSettle();

      // Verifies navigation to Screen 005 Trust screen
      expect(find.byType(OnboardingTrustScreen), findsOneWidget);
      expect(find.text(AppStrings.onboardingTrustHeading), findsOneWidget);
    });

    testWidgets(
      '"Back" button returns to Screen 003 — Identity when opened from Screen 003',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingIdentityScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        // Navigate to Screen 004
        final continueFinder = find.text(AppStrings.continueAction);
        await tester.ensureVisible(continueFinder);
        await tester.tap(continueFinder);
        await tester.pumpAndSettle();

        // Verifies we are on Screen 004
        expect(find.byType(OnboardingSecurityScreen), findsOneWidget);

        // Tap bottom "Back" button
        final backButtonFinder = find.widgetWithText(
          OutlinedButton,
          AppStrings.backAction,
        );
        expect(backButtonFinder, findsOneWidget);
        await tester.ensureVisible(backButtonFinder);
        await tester.tap(backButtonFinder);
        await tester.pumpAndSettle();

        // Verifies we returned to Screen 003
        expect(find.byType(OnboardingIdentityScreen), findsOneWidget);
        expect(find.text(AppStrings.onboardingIdentityHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Top header back button returns to Screen 003 when opened from Screen 003',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingIdentityScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        // Navigate to Screen 004
        final continueFinder = find.text(AppStrings.continueAction);
        await tester.ensureVisible(continueFinder);
        await tester.tap(continueFinder);
        await tester.pumpAndSettle();

        expect(find.byType(OnboardingSecurityScreen), findsOneWidget);

        // Tap top header back icon button
        final topBackFinder = find.byTooltip(AppStrings.backTooltip);
        expect(topBackFinder, findsOneWidget);
        await tester.tap(topBackFinder);
        await tester.pumpAndSettle();

        // Verifies we returned to Screen 003
        expect(find.byType(OnboardingIdentityScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Back button replaces route to Screen 003 when opened standalone',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingSecurityScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        final backButtonFinder = find.widgetWithText(
          OutlinedButton,
          AppStrings.backAction,
        );
        expect(backButtonFinder, findsOneWidget);
        await tester.ensureVisible(backButtonFinder);
        await tester.tap(backButtonFinder);
        await tester.pumpAndSettle();

        // Navigated to Screen 003 fallback
        expect(find.byType(OnboardingIdentityScreen), findsOneWidget);
      },
    );

    testWidgets('"Skip for now" button navigates to user-entry sign-in route', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: const OnboardingSecurityScreen(),
          onGenerateRoute: AppRoutes.onGenerateRoute,
        ),
      );

      await tester.pumpAndSettle();

      final skipFinder = find.text(AppStrings.skipForNow);
      await tester.ensureVisible(skipFinder);
      await tester.tap(skipFinder);
      await tester.pumpAndSettle();

      // Verifies navigation to sign-in destination (LoginScreen)
      expect(find.byType(LoginScreen), findsOneWidget);
      expect(find.text(AppStrings.loginHeading), findsOneWidget);
    });

    testWidgets(
      'Renders OnboardingSecurityScreen without overflow on varied screen sizes',
      (WidgetTester tester) async {
        final screenSizes = [
          const Size(320, 568), // Small mobile (iPhone SE)
          const Size(390, 844), // Standard mobile (iPhone 13/14)
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const OnboardingSecurityScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(
            find.text(AppStrings.onboardingSecurityHeading),
            findsOneWidget,
          );
          expect(find.text(AppStrings.continueAction), findsOneWidget);
          expect(find.text(AppStrings.step2Of3), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons support keyboard navigation and focus on Screen 004',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingSecurityScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        // Press Tab key repeatedly to test traversal
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        // Verify widget remains stable and interactive
        expect(find.byType(OnboardingSecurityScreen), findsOneWidget);
      },
    );
  });

  group('Screen 005 — Onboarding: Trust Screen Tests', () {
    testWidgets(
      'Renders progress indicator, illustration, heading, description, 3 features, disclaimer, and actions',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingTrustScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        // Top progress indicator showing Step 3 of 3
        expect(find.byType(OnboardingProgressIndicator), findsOneWidget);
        expect(find.text(AppStrings.step3Of3), findsOneWidget);

        // Back navigation button
        expect(find.byTooltip(AppStrings.backTooltip), findsOneWidget);

        // Visual representing digital identity card, verification checkmark, and human-review symbol
        expect(find.byType(TrustVerificationVisual), findsOneWidget);

        // Heading and description
        expect(find.text(AppStrings.onboardingTrustHeading), findsOneWidget);
        expect(
          find.text(AppStrings.onboardingTrustDescription),
          findsOneWidget,
        );

        // Three short feature points
        expect(find.byType(IdentityBenefitItem), findsNWidgets(3));
        expect(find.text(AppStrings.onboardingTrustFeature1), findsOneWidget);
        expect(find.text(AppStrings.onboardingTrustFeature2), findsOneWidget);
        expect(find.text(AppStrings.onboardingTrustFeature3), findsOneWidget);

        // Transparency notice / disclaimer
        expect(find.text(AppStrings.onboardingTrustDisclaimer), findsOneWidget);

        // Primary and secondary action buttons
        expect(find.text(AppStrings.getStarted), findsOneWidget);
        expect(find.text(AppStrings.backAction), findsOneWidget);
      },
    );

    testWidgets(
      '"Get Started" button navigates to Screen 006 — Language Selection route',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingTrustScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        final getStartedFinder = find.widgetWithText(
          ElevatedButton,
          AppStrings.getStarted,
        );
        await tester.ensureVisible(getStartedFinder);
        await tester.tap(getStartedFinder);
        await tester.pumpAndSettle();

        // Verifies navigation to Screen 006 Language Selection
        expect(find.byType(LanguageSelectionScreen), findsOneWidget);
        expect(
          find.text(AppStrings.languageSelectionHeading),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      '"Back" button returns to Screen 004 — Security when opened from Screen 004',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingSecurityScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        // Navigate to Screen 005
        final continueFinder = find.text(AppStrings.continueAction);
        await tester.ensureVisible(continueFinder);
        await tester.tap(continueFinder);
        await tester.pumpAndSettle();

        // Verifies we are on Screen 005
        expect(find.byType(OnboardingTrustScreen), findsOneWidget);

        // Tap bottom "Back" button
        final backButtonFinder = find.widgetWithText(
          OutlinedButton,
          AppStrings.backAction,
        );
        expect(backButtonFinder, findsOneWidget);
        await tester.ensureVisible(backButtonFinder);
        await tester.tap(backButtonFinder);
        await tester.pumpAndSettle();

        // Verifies we returned to Screen 004
        expect(find.byType(OnboardingSecurityScreen), findsOneWidget);
        expect(find.text(AppStrings.onboardingSecurityHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Top header back button returns to Screen 004 when opened from Screen 004',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingSecurityScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        // Navigate to Screen 005
        final continueFinder = find.text(AppStrings.continueAction);
        await tester.ensureVisible(continueFinder);
        await tester.tap(continueFinder);
        await tester.pumpAndSettle();

        expect(find.byType(OnboardingTrustScreen), findsOneWidget);

        // Tap top header back icon button
        final topBackFinder = find.byTooltip(AppStrings.backTooltip);
        expect(topBackFinder, findsOneWidget);
        await tester.tap(topBackFinder);
        await tester.pumpAndSettle();

        // Verifies we returned to Screen 004
        expect(find.byType(OnboardingSecurityScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Back button replaces route to Screen 004 when opened standalone',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingTrustScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        final backButtonFinder = find.widgetWithText(
          OutlinedButton,
          AppStrings.backAction,
        );
        expect(backButtonFinder, findsOneWidget);
        await tester.ensureVisible(backButtonFinder);
        await tester.tap(backButtonFinder);
        await tester.pumpAndSettle();

        // Navigated to Screen 004 fallback
        expect(find.byType(OnboardingSecurityScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Full onboarding traversal from Welcome -> 003 -> 004 -> 005 -> 006',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const WelcomeScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        // Step 0: Welcome Screen -> Tap Get Started
        final welcomeStart = find.text(AppStrings.getStarted);
        await tester.ensureVisible(welcomeStart);
        await tester.tap(welcomeStart);
        await tester.pumpAndSettle();
        expect(find.byType(OnboardingIdentityScreen), findsOneWidget);

        // Step 1: Screen 003 (Identity) -> Tap Continue
        final step1Continue = find.text(AppStrings.continueAction);
        await tester.ensureVisible(step1Continue);
        await tester.tap(step1Continue);
        await tester.pumpAndSettle();
        expect(find.byType(OnboardingSecurityScreen), findsOneWidget);

        // Step 2: Screen 004 (Security) -> Tap Continue
        final step2Continue = find.text(AppStrings.continueAction);
        await tester.ensureVisible(step2Continue);
        await tester.tap(step2Continue);
        await tester.pumpAndSettle();
        expect(find.byType(OnboardingTrustScreen), findsOneWidget);

        // Step 3: Screen 005 (Trust) -> Tap Get Started
        final step3GetStarted = find.widgetWithText(
          ElevatedButton,
          AppStrings.getStarted,
        );
        await tester.ensureVisible(step3GetStarted);
        await tester.tap(step3GetStarted);
        await tester.pumpAndSettle();

        // Step 4: Screen 006 Language Selection
        expect(find.byType(LanguageSelectionScreen), findsOneWidget);
        expect(
          find.text(AppStrings.languageSelectionHeading),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Renders OnboardingTrustScreen without overflow on varied screen sizes',
      (WidgetTester tester) async {
        final screenSizes = [
          const Size(320, 568), // Small mobile (iPhone SE)
          const Size(390, 844), // Standard mobile (iPhone 13/14)
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const OnboardingTrustScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.text(AppStrings.onboardingTrustHeading), findsOneWidget);
          expect(find.text(AppStrings.getStarted), findsOneWidget);
          expect(find.text(AppStrings.step3Of3), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons support keyboard navigation and focus on Screen 005',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingTrustScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );

        await tester.pumpAndSettle();

        // Press Tab key repeatedly to test traversal
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        // Verify widget remains stable and interactive
        expect(find.byType(OnboardingTrustScreen), findsOneWidget);
      },
    );
  });

  group('Screen 006 — Language Selection Screen Tests', () {
    setUp(() {
      LanguageController.instance.resetToDefault();
    });

    testWidgets(
      'Renders heading, subtitle, Tamil card, English card, and Continue button',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LanguageSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Brand & Visual Emblem
        expect(find.byIcon(Icons.language_rounded), findsOneWidget);

        // Heading & Subtitle
        expect(find.text(AppStrings.languageSelectionHeading), findsOneWidget);
        expect(
          find.text(AppStrings.languageSelectionSubtitle),
          findsOneWidget,
        );

        // Language Option Cards
        expect(
          find.text(AppStrings.languageTamil),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.languageEnglish),
          findsOneWidget,
        );

        // Tamil character and English emblem rendered
        expect(find.text('த'), findsOneWidget);
        expect(find.text('EN'), findsOneWidget);
        expect(find.text('தமிழ் எழுத்துமுறை • Native UI'), findsOneWidget);

        // Action Buttons
        expect(find.text(AppStrings.continueAction), findsOneWidget);
        expect(find.byIcon(Icons.arrow_back_rounded), findsOneWidget);
      },
    );

    testWidgets(
      'Allows exactly one language to be selected at a time and toggles selection',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LanguageSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Default: English is selected
        final englishCard = find.ancestor(
          of: find.text(AppStrings.languageEnglish),
          matching: find.byType(LanguageOptionCard),
        );
        final tamilCard = find.ancestor(
          of: find.text(AppStrings.languageTamil),
          matching: find.byType(LanguageOptionCard),
        );

        expect(
          tester.widget<LanguageOptionCard>(englishCard).isSelected,
          isTrue,
        );
        expect(
          tester.widget<LanguageOptionCard>(tamilCard).isSelected,
          isFalse,
        );

        // Tap Tamil card to select it
        await tester.tap(tamilCard);
        await tester.pumpAndSettle();

        // Tamil is selected, English is not
        expect(
          tester.widget<LanguageOptionCard>(tamilCard).isSelected,
          isTrue,
        );
        expect(
          tester.widget<LanguageOptionCard>(englishCard).isSelected,
          isFalse,
        );

        // Tap English card to reselect English
        await tester.tap(englishCard);
        await tester.pumpAndSettle();

        // English is selected, Tamil is not
        expect(
          tester.widget<LanguageOptionCard>(englishCard).isSelected,
          isTrue,
        );
        expect(
          tester.widget<LanguageOptionCard>(tamilCard).isSelected,
          isFalse,
        );
      },
    );

    testWidgets(
      '"Continue" button saves Tamil preference and navigates to Screen 007 — Country & Region',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LanguageSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Select Tamil
        final tamilCard = find.text(AppStrings.languageTamil);
        await tester.tap(tamilCard);
        await tester.pumpAndSettle();

        // Tap Continue
        final continueButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueButton);
        await tester.tap(continueButton);
        await tester.pumpAndSettle();

        // Preference saved to LanguageController
        expect(LanguageController.instance.currentLanguageCode, 'ta');

        // Navigates to Screen 007 route
        expect(find.byType(CountryRegionScreen), findsOneWidget);
        expect(
          find.text(AppStrings.countryRegionHeading),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      '"Continue" button saves English preference and navigates to Screen 007 — Country & Region',
      (WidgetTester tester) async {
        // Pre-set to Tamil to test switching to English
        LanguageController.instance.setLanguage('ta');

        await tester.pumpWidget(
          MaterialApp(
            home: const LanguageSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Select English
        final englishCard = find.text(AppStrings.languageEnglish);
        await tester.tap(englishCard);
        await tester.pumpAndSettle();

        // Tap Continue
        final continueButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueButton);
        await tester.tap(continueButton);
        await tester.pumpAndSettle();

        // Preference saved to LanguageController
        expect(LanguageController.instance.currentLanguageCode, 'en');

        // Navigates to Screen 007 route
        expect(find.byType(CountryRegionScreen), findsOneWidget);
        expect(
          find.text(AppStrings.countryRegionHeading),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Top back button returns to Screen 005 — Trust when opened from Screen 005',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingTrustScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Navigate to Screen 006
        final getStarted = find.widgetWithText(
          ElevatedButton,
          AppStrings.getStarted,
        );
        await tester.ensureVisible(getStarted);
        await tester.tap(getStarted);
        await tester.pumpAndSettle();

        expect(find.byType(LanguageSelectionScreen), findsOneWidget);

        // Tap back
        final backButton = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backButton);
        await tester.pumpAndSettle();

        // Returned to Screen 005
        expect(find.byType(OnboardingTrustScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Top back button replaces route to Screen 005 when opened standalone',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LanguageSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final backButton = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backButton);
        await tester.pumpAndSettle();

        // Falls back to Screen 005
        expect(find.byType(OnboardingTrustScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Renders LanguageSelectionScreen without overflow on varied screen sizes',
      (WidgetTester tester) async {
        final screenSizes = [
          const Size(320, 568), // Small mobile (iPhone SE)
          const Size(390, 844), // Standard mobile (iPhone 13/14)
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const LanguageSelectionScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(
            find.text(AppStrings.languageSelectionHeading),
            findsOneWidget,
          );
          expect(
            find.text(AppStrings.languageTamil),
            findsOneWidget,
          );
          expect(
            find.text(AppStrings.languageEnglish),
            findsOneWidget,
          );
          expect(find.text(AppStrings.continueAction), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons and language cards support keyboard navigation and focus on Screen 006',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LanguageSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(LanguageSelectionScreen), findsOneWidget);
      },
    );

    testWidgets(
      'App applies chosen language reactively across MaterialApp',
      (WidgetTester tester) async {
        await tester.pumpWidget(const AiTrustApp());
        await tester.pumpAndSettle();

        // Change language via controller
        LanguageController.instance.setLanguage('ta');
        await tester.pumpAndSettle();

        final app = tester.widget<MaterialApp>(find.byType(MaterialApp));
        expect(app.locale, const Locale('ta'));

        LanguageController.instance.setLanguage('en');
        await tester.pumpAndSettle();

        final appEn = tester.widget<MaterialApp>(find.byType(MaterialApp));
        expect(appEn.locale, const Locale('en'));
      },
    );
  });

  group('Screen 007 — Country & Region Selection Screen Tests', () {
    setUp(() {
      LocationPreferencesController.instance.resetToDefault();
    });

    testWidgets(
      'Renders heading, subtitle, country selector, region selector, disclaimer, and Continue button',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CountryRegionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Visual Emblem
        expect(find.byIcon(Icons.public_rounded), findsOneWidget);

        // Heading & Subtitle
        expect(find.text(AppStrings.countryRegionHeading), findsOneWidget);
        expect(find.text(AppStrings.countryRegionSubtitle), findsOneWidget);

        // Default suggested country is India
        expect(find.text('India'), findsOneWidget);
        expect(find.text('IN'), findsOneWidget);
        expect(find.text('🇮🇳'), findsOneWidget);

        // Region Selector with empty placeholder
        expect(
          find.text(AppStrings.stateRegionPlaceholder),
          findsOneWidget,
        );

        // Regional Compliance & Privacy Disclaimer
        expect(find.text(AppStrings.locationDisclaimer), findsOneWidget);

        // Primary Action Button & Back Button
        expect(find.text(AppStrings.continueAction), findsOneWidget);
        expect(find.byIcon(Icons.arrow_back_rounded), findsOneWidget);
      },
    );

    testWidgets(
      'India is suggested by default and supports selecting states and union territories',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CountryRegionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap Region selector to open modal
        final regionField = find.byType(RegionSelectorField);
        await tester.ensureVisible(regionField);
        await tester.tap(regionField);
        await tester.pumpAndSettle();

        // Verify SearchableRegionModal is shown
        expect(find.byType(SearchableRegionModal), findsOneWidget);
        expect(find.text('STATES (28)'), findsOneWidget);

        // Search for a Union Territory (Delhi) to verify UT support
        final searchField = find.byType(TextField);
        await tester.enterText(searchField, 'Delhi');
        await tester.pumpAndSettle();
        expect(find.text('Delhi (NCT)'), findsOneWidget);
        expect(find.text(AppStrings.unionTerritoryBadge), findsOneWidget);

        // Now search and select Tamil Nadu
        await tester.enterText(searchField, 'Tamil');
        await tester.pumpAndSettle();
        final tamilNaduTile = find.widgetWithText(InkWell, 'Tamil Nadu');
        expect(tamilNaduTile, findsOneWidget);
        await tester.tap(tamilNaduTile);
        await tester.pumpAndSettle();

        // Modal closed and RegionSelectorField now displays Tamil Nadu
        expect(find.byType(SearchableRegionModal), findsNothing);
        expect(find.text('Tamil Nadu'), findsOneWidget);
      },
    );

    testWidgets(
      'Searches and selects a different country via SearchableCountryModal',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CountryRegionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap Country selector to open modal
        final countryField = find.byType(CountrySelectorField);
        await tester.tap(countryField);
        await tester.pumpAndSettle();

        expect(find.byType(SearchableCountryModal), findsOneWidget);
        expect(find.text(AppStrings.suggestedBadge), findsOneWidget);

        // Search for United States
        final searchField = find.byType(TextField);
        await tester.enterText(searchField, 'United States');
        await tester.pumpAndSettle();

        // Tap United States in the list
        final usTile = find.widgetWithText(InkWell, 'United States');
        expect(usTile, findsOneWidget);
        await tester.tap(usTile);
        await tester.pumpAndSettle();

        // Modal closed and CountrySelectorField now displays United States
        expect(find.byType(SearchableCountryModal), findsNothing);
        expect(find.text('United States'), findsOneWidget);
        expect(find.text('US'), findsOneWidget);
        expect(find.text('🇺🇸'), findsOneWidget);
      },
    );

    testWidgets(
      'Resets previously selected region when country changes',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CountryRegionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // 1. Select Tamil Nadu under India using search
        await tester.tap(find.byType(RegionSelectorField));
        await tester.pumpAndSettle();
        await tester.enterText(find.byType(TextField), 'Tamil');
        await tester.pumpAndSettle();
        await tester.tap(find.widgetWithText(InkWell, 'Tamil Nadu'));
        await tester.pumpAndSettle();
        expect(find.text('Tamil Nadu'), findsOneWidget);

        // 2. Change Country to United States
        await tester.tap(find.byType(CountrySelectorField));
        await tester.pumpAndSettle();
        await tester.enterText(find.byType(TextField), 'United States');
        await tester.pumpAndSettle();
        await tester.tap(find.widgetWithText(InkWell, 'United States'));
        await tester.pumpAndSettle();

        // 3. Verify country is updated and region is reset to placeholder
        expect(find.text('United States'), findsOneWidget);
        expect(find.text('Tamil Nadu'), findsNothing);
        expect(
          find.text(AppStrings.stateRegionPlaceholder),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Validates required selections before continuing',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CountryRegionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // India is selected, but region is empty -> tap Continue
        final continueButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueButton);
        await tester.tap(continueButton);
        await tester.pumpAndSettle();

        // Verification error displayed and screen remains on CountryRegionScreen
        expect(
          find.text(AppStrings.regionRequiredError),
          findsOneWidget,
        );
        expect(find.byType(CountryRegionScreen), findsOneWidget);
        expect(find.byType(RoutePlaceholderScreen), findsNothing);
      },
    );

    testWidgets(
      'Saves location preference and navigates to Screen 008 — User Type Selection',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CountryRegionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Select Tamil Nadu using search
        await tester.tap(find.byType(RegionSelectorField));
        await tester.pumpAndSettle();
        await tester.enterText(find.byType(TextField), 'Tamil');
        await tester.pumpAndSettle();
        await tester.tap(find.widgetWithText(InkWell, 'Tamil Nadu'));
        await tester.pumpAndSettle();

        // Tap Continue
        final continueButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueButton);
        await tester.tap(continueButton);
        await tester.pumpAndSettle();

        // Location saved in controller
        expect(
          LocationPreferencesController.instance.savedCountry?.code,
          'IN',
        );
        expect(
          LocationPreferencesController.instance.savedRegion?.name,
          'Tamil Nadu',
        );

        // Navigated to Screen 008 User Type Selection route
        expect(find.byType(UserTypeSelectionScreen), findsOneWidget);
        expect(
          find.text(AppStrings.userTypeHeading),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Top back button returns to Screen 006 — Language Selection when opened from Screen 006',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LanguageSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Navigate forward from Screen 006 to Screen 007
        final continueBtn = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueBtn);
        await tester.tap(continueBtn);
        await tester.pumpAndSettle();

        expect(find.byType(CountryRegionScreen), findsOneWidget);

        // Tap top back button
        final backButton = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backButton);
        await tester.pumpAndSettle();

        // Returned cleanly to Screen 006
        expect(find.byType(LanguageSelectionScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Top back button replaces route to Screen 006 when opened standalone',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CountryRegionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final backButton = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backButton);
        await tester.pumpAndSettle();

        // Replaced route to Screen 006
        expect(find.byType(LanguageSelectionScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Search modals display empty states when query matches no results',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CountryRegionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Open country search modal and enter unknown query
        await tester.tap(find.byType(CountrySelectorField));
        await tester.pumpAndSettle();

        await tester.enterText(find.byType(TextField), 'UnknownCountryXYZ');
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.noCountriesFound), findsOneWidget);

        // Clear query using button
        await tester.tap(find.widgetWithText(OutlinedButton, AppStrings.clearSearch));
        await tester.pumpAndSettle();
        expect(find.text('India'), findsWidgets);

        // Close country modal safely
        Navigator.of(tester.element(find.byType(SearchableCountryModal))).pop();
        await tester.pumpAndSettle();

        // Open region search modal and enter unknown query
        await tester.tap(find.byType(RegionSelectorField));
        await tester.pumpAndSettle();

        await tester.enterText(find.byType(TextField), 'UnknownRegionXYZ');
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.noRegionsFound), findsOneWidget);

        // Close region modal safely
        Navigator.of(tester.element(find.byType(SearchableRegionModal))).pop();
        await tester.pumpAndSettle();
      },
    );

    testWidgets(
      'Renders CountryRegionScreen without overflow on varied screen sizes',
      (WidgetTester tester) async {
        final screenSizes = [
          const Size(320, 568), // Small mobile (iPhone SE)
          const Size(390, 844), // Standard mobile (iPhone 13/14)
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const CountryRegionScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(
            find.text(AppStrings.countryRegionHeading),
            findsOneWidget,
          );
          expect(find.byType(CountrySelectorField), findsOneWidget);
          expect(find.byType(RegionSelectorField), findsOneWidget);
          expect(find.text(AppStrings.continueAction), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons and selectors support keyboard navigation and focus on Screen 007',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CountryRegionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(CountryRegionScreen), findsOneWidget);
      },
    );
  });

  group('Screen 008 — User Type Selection Screen Tests', () {
    setUp(() {
      UserTypeController.instance.resetToDefault();
    });

    testWidgets(
      'Renders heading, subtitle, three role option cards, authorization notice, and Continue button',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const UserTypeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Visual Emblem
        expect(find.byIcon(Icons.badge_rounded), findsOneWidget);

        // Heading & Subtitle
        expect(find.text(AppStrings.userTypeHeading), findsOneWidget);
        expect(find.text(AppStrings.userTypeSubtitle), findsOneWidget);

        // Three Role Option Cards
        expect(find.text(AppStrings.individualTitle), findsOneWidget);
        expect(find.text(AppStrings.individualDescription), findsOneWidget);
        expect(find.byIcon(Icons.person_rounded), findsOneWidget);

        expect(find.text(AppStrings.organizationTitle), findsOneWidget);
        expect(find.text(AppStrings.organizationDescription), findsOneWidget);
        expect(find.byIcon(Icons.business_rounded), findsOneWidget);

        expect(find.text(AppStrings.reviewerTitle), findsOneWidget);
        expect(find.text(AppStrings.reviewerDescription), findsOneWidget);
        expect(find.byIcon(Icons.fact_check_rounded), findsOneWidget);

        // Auth Required Badges (for Organization and Reviewer)
        expect(find.text('AUTH REQUIRED'), findsNWidgets(2));

        // Authorization Notice Banner
        expect(find.text(AppStrings.userTypeNotice), findsOneWidget);

        // Continue Button and Back Button
        expect(find.text(AppStrings.continueAction), findsOneWidget);
        expect(find.byIcon(Icons.arrow_back_rounded), findsOneWidget);
      },
    );

    testWidgets(
      'Allows exactly one role selection at a time and toggles selection cleanly',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const UserTypeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final individualCardFinder = find.ancestor(
          of: find.text(AppStrings.individualTitle),
          matching: find.byType(UserTypeCard),
        );
        final organizationCardFinder = find.ancestor(
          of: find.text(AppStrings.organizationTitle),
          matching: find.byType(UserTypeCard),
        );
        final reviewerCardFinder = find.ancestor(
          of: find.text(AppStrings.reviewerTitle),
          matching: find.byType(UserTypeCard),
        );

        // Initially no card is selected
        expect(
          tester.widget<UserTypeCard>(individualCardFinder).isSelected,
          isFalse,
        );
        expect(
          tester.widget<UserTypeCard>(organizationCardFinder).isSelected,
          isFalse,
        );
        expect(
          tester.widget<UserTypeCard>(reviewerCardFinder).isSelected,
          isFalse,
        );

        // Select Individual
        await tester.tap(individualCardFinder);
        await tester.pumpAndSettle();

        expect(
          tester.widget<UserTypeCard>(individualCardFinder).isSelected,
          isTrue,
        );
        expect(
          tester.widget<UserTypeCard>(organizationCardFinder).isSelected,
          isFalse,
        );
        expect(
          tester.widget<UserTypeCard>(reviewerCardFinder).isSelected,
          isFalse,
        );

        // Select Organization
        await tester.ensureVisible(organizationCardFinder);
        await tester.tap(organizationCardFinder);
        await tester.pumpAndSettle();

        expect(
          tester.widget<UserTypeCard>(individualCardFinder).isSelected,
          isFalse,
        );
        expect(
          tester.widget<UserTypeCard>(organizationCardFinder).isSelected,
          isTrue,
        );
        expect(
          tester.widget<UserTypeCard>(reviewerCardFinder).isSelected,
          isFalse,
        );

        // Select Reviewer
        await tester.ensureVisible(reviewerCardFinder);
        await tester.tap(reviewerCardFinder);
        await tester.pumpAndSettle();

        expect(
          tester.widget<UserTypeCard>(individualCardFinder).isSelected,
          isFalse,
        );
        expect(
          tester.widget<UserTypeCard>(organizationCardFinder).isSelected,
          isFalse,
        );
        expect(
          tester.widget<UserTypeCard>(reviewerCardFinder).isSelected,
          isTrue,
        );
      },
    );

    testWidgets(
      'Validates that a selection is required before continuing',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const UserTypeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap Continue with no selection
        final continueButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueButton);
        await tester.tap(continueButton);
        await tester.pumpAndSettle();

        // Error message is displayed and screen does not navigate
        expect(find.text(AppStrings.userTypeRequiredError), findsOneWidget);
        expect(find.byType(UserTypeSelectionScreen), findsOneWidget);
        expect(find.byType(RoutePlaceholderScreen), findsNothing);
      },
    );

    testWidgets(
      'Selecting Individual preserves selection and navigates to Screen 009 — Purpose Selection',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const UserTypeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap Individual
        final individualTile = find.text(AppStrings.individualTitle);
        await tester.ensureVisible(individualTile);
        await tester.tap(individualTile);
        await tester.pumpAndSettle();

        // Tap Continue
        final continueButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueButton);
        await tester.tap(continueButton);
        await tester.pumpAndSettle();

        // Preserved in controller
        expect(
          UserTypeController.instance.selectedUserType,
          UserType.individual,
        );

        // Navigates to Screen 009 Purpose Selection route
        expect(find.byType(PurposeSelectionScreen), findsOneWidget);
        expect(
          find.text(AppStrings.purposeHeading),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Selecting Organization preserves selection and navigates to Screen 009',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const UserTypeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap Organization
        final orgTile = find.text(AppStrings.organizationTitle);
        await tester.ensureVisible(orgTile);
        await tester.tap(orgTile);
        await tester.pumpAndSettle();

        // Tap Continue
        final continueButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueButton);
        await tester.tap(continueButton);
        await tester.pumpAndSettle();

        // Preserved in controller
        expect(
          UserTypeController.instance.selectedUserType,
          UserType.organization,
        );

        // Navigates to Screen 009 Purpose Selection route
        expect(find.byType(PurposeSelectionScreen), findsOneWidget);
        expect(
          find.text(AppStrings.purposeHeading),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Selecting Reviewer preserves selection and navigates to Screen 009',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const UserTypeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap Reviewer
        final reviewerTile = find.text(AppStrings.reviewerTitle);
        await tester.ensureVisible(reviewerTile);
        await tester.tap(reviewerTile);
        await tester.pumpAndSettle();

        // Tap Continue
        final continueButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueButton);
        await tester.tap(continueButton);
        await tester.pumpAndSettle();

        // Preserved in controller
        expect(
          UserTypeController.instance.selectedUserType,
          UserType.reviewer,
        );

        // Navigates to Screen 009 Purpose Selection route
        expect(find.byType(PurposeSelectionScreen), findsOneWidget);
        expect(
          find.text(AppStrings.purposeHeading),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Permission Safeguards: Role selection never grants privileged platform permissions on client',
      (WidgetTester tester) async {
        // Test Organization
        UserTypeController.instance.selectUserType(UserType.organization);
        expect(UserTypeController.instance.hasPrivilegedAccess, isFalse);
        expect(UserTypeController.instance.isBackendAuthorized, isFalse);

        // Test Reviewer
        UserTypeController.instance.selectUserType(UserType.reviewer);
        expect(UserTypeController.instance.hasPrivilegedAccess, isFalse);
        expect(UserTypeController.instance.isBackendAuthorized, isFalse);

        // Test Individual
        UserTypeController.instance.selectUserType(UserType.individual);
        expect(UserTypeController.instance.hasPrivilegedAccess, isFalse);
        expect(UserTypeController.instance.isBackendAuthorized, isFalse);
      },
    );

    testWidgets(
      'Top back button returns to Screen 007 — Country & Region when opened from Screen 007',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CountryRegionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Select region under India and navigate forward to Screen 008
        await tester.tap(find.byType(RegionSelectorField));
        await tester.pumpAndSettle();
        await tester.enterText(find.byType(TextField), 'Tamil');
        await tester.pumpAndSettle();
        await tester.tap(find.widgetWithText(InkWell, 'Tamil Nadu'));
        await tester.pumpAndSettle();

        final continueBtn = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueBtn);
        await tester.tap(continueBtn);
        await tester.pumpAndSettle();

        expect(find.byType(UserTypeSelectionScreen), findsOneWidget);

        // Tap top back button
        final backButton = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backButton);
        await tester.pumpAndSettle();

        // Returned cleanly to Screen 007
        expect(find.byType(CountryRegionScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Top back button replaces route to Screen 007 when opened standalone',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const UserTypeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final backButton = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backButton);
        await tester.pumpAndSettle();

        // Replaced route to Screen 007
        expect(find.byType(CountryRegionScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Renders UserTypeSelectionScreen without overflow on varied screen sizes',
      (WidgetTester tester) async {
        final screenSizes = [
          const Size(320, 568), // Small mobile (iPhone SE)
          const Size(390, 844), // Standard mobile (iPhone 13/14)
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const UserTypeSelectionScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(
            find.text(AppStrings.userTypeHeading),
            findsOneWidget,
          );
          expect(find.text(AppStrings.individualTitle), findsOneWidget);
          expect(find.text(AppStrings.organizationTitle), findsOneWidget);
          expect(find.text(AppStrings.reviewerTitle), findsOneWidget);
          expect(find.text(AppStrings.continueAction), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons and role cards support keyboard navigation and focus on Screen 008',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const UserTypeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(UserTypeSelectionScreen), findsOneWidget);
      },
    );
  });

  group('Screen 009 — Purpose Selection Screen Tests', () {
    setUp(() {
      PurposeSelectionController.instance.resetToDefault();
    });

    tearDown(() {
      PurposeSelectionController.instance.resetToDefault();
    });

    testWidgets(
      'Renders heading, subtitle, six purpose cards, visual emblem, disclaimer, and Continue button',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const PurposeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Typography
        expect(find.text(AppStrings.purposeHeading), findsOneWidget);
        expect(find.text(AppStrings.purposeSubtitle), findsOneWidget);

        // Visual Emblem & Top Back
        expect(find.byTooltip(AppStrings.backTooltip), findsOneWidget);
        expect(
          find.bySemanticsLabel(AppStrings.purposeVisualSemantic),
          findsOneWidget,
        );

        // Six Purpose Cards
        expect(find.text(AppStrings.purposeIdentityTitle), findsOneWidget);
        expect(find.text(AppStrings.purposeEmploymentTitle), findsOneWidget);
        expect(find.text(AppStrings.purposeEducationTitle), findsOneWidget);
        expect(find.text(AppStrings.purposeOrganizationTitle), findsOneWidget);
        expect(find.text(AppStrings.purposeDigitalDocumentsTitle), findsOneWidget);
        expect(find.text(AppStrings.purposeOtherTitle), findsOneWidget);

        // Badges
        expect(find.text(AppStrings.badgeSupported), findsNWidgets(2));
        expect(find.text(AppStrings.badgeIntegrationRequired), findsNWidgets(2));
        expect(find.text(AppStrings.badgeAuthRequired), findsOneWidget);
        expect(find.text(AppStrings.badgeGeneral), findsOneWidget);

        // Disclaimer notice & action button
        final disclaimerFinder = find.text(AppStrings.purposeNotice);
        await tester.ensureVisible(disclaimerFinder);
        expect(disclaimerFinder, findsOneWidget);

        final continueButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueButton);
        expect(continueButton, findsOneWidget);
      },
    );

    testWidgets(
      'Allows single purpose selection and updates card selection state',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const PurposeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Initially no purpose is selected in controller
        expect(PurposeSelectionController.instance.hasSelection, isFalse);

        // Tap Identity Verification card
        final identityCard = find.text(AppStrings.purposeIdentityTitle);
        await tester.ensureVisible(identityCard);
        await tester.tap(identityCard);
        await tester.pumpAndSettle();

        // Check icon appears on selected card
        expect(find.byIcon(Icons.check_rounded), findsOneWidget);

        // Semantics verification
        expect(
          find.bySemanticsLabel(RegExp(r'Identity Verification.*Selected')),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Toggles selection cleanly between multiple purpose options',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const PurposeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Select Identity Verification
        final identityCard = find.text(AppStrings.purposeIdentityTitle);
        await tester.ensureVisible(identityCard);
        await tester.tap(identityCard);
        await tester.pumpAndSettle();
        expect(find.byIcon(Icons.check_rounded), findsOneWidget);

        // Select Employment Verification
        final employmentCard = find.text(AppStrings.purposeEmploymentTitle);
        await tester.ensureVisible(employmentCard);
        await tester.tap(employmentCard);
        await tester.pumpAndSettle();

        // Only one card selected at a time
        expect(find.byIcon(Icons.check_rounded), findsOneWidget);

        // Select Education Verification
        final educationCard = find.text(AppStrings.purposeEducationTitle);
        await tester.ensureVisible(educationCard);
        await tester.tap(educationCard);
        await tester.pumpAndSettle();
        expect(find.byIcon(Icons.check_rounded), findsOneWidget);

        // Select Other Purpose
        final otherCard = find.text(AppStrings.purposeOtherTitle);
        await tester.ensureVisible(otherCard);
        await tester.tap(otherCard);
        await tester.pumpAndSettle();
        expect(find.byIcon(Icons.check_rounded), findsOneWidget);
      },
    );

    testWidgets(
      'Validates that a selection is required before continuing and displays error message',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const PurposeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Ensure no selection
        expect(PurposeSelectionController.instance.hasSelection, isFalse);

        // Tap Continue without selecting anything
        final continueButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueButton);
        await tester.tap(continueButton);
        await tester.pumpAndSettle();

        // Validation error displayed
        expect(find.text(AppStrings.purposeRequiredError), findsOneWidget);
        expect(find.byIcon(Icons.error_outline_rounded), findsOneWidget);

        // Selecting a purpose clears the error
        final identityCard = find.text(AppStrings.purposeIdentityTitle);
        await tester.ensureVisible(identityCard);
        await tester.tap(identityCard);
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.purposeRequiredError), findsNothing);
      },
    );

    testWidgets(
      'Selecting Identity Verification preserves selection and navigates to Screen 010 — Onboarding Complete',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const PurposeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap Identity Verification
        final identityCard = find.text(AppStrings.purposeIdentityTitle);
        await tester.ensureVisible(identityCard);
        await tester.tap(identityCard);
        await tester.pumpAndSettle();

        // Tap Continue
        final continueButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueButton);
        await tester.tap(continueButton);
        await tester.pumpAndSettle();

        // Preserved in controller
        expect(
          PurposeSelectionController.instance.selectedPurpose,
          PlatformPurpose.identityVerification,
        );

        // Navigates to Screen 010 Onboarding Complete
        expect(find.byType(OnboardingCompleteScreen), findsOneWidget);
        expect(
          find.text(AppStrings.onboardingCompleteHeading),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Selecting Employment Verification displays integration notice without claiming automated verification, preserves selection, and navigates to Screen 010',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const PurposeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap Employment Verification
        final employmentCard = find.text(AppStrings.purposeEmploymentTitle);
        await tester.ensureVisible(employmentCard);
        await tester.tap(employmentCard);
        await tester.pumpAndSettle();

        // Integration notice banner displayed
        expect(find.text(AppStrings.integrationNoticeHeader), findsOneWidget);
        expect(
          find.text(AppStrings.employmentIntegrationNotice),
          findsOneWidget,
        );

        // Controller confirms direct automated verification is false
        expect(
          PurposeSelectionController.instance.isPurposeDirectlySupported(
            PlatformPurpose.employmentVerification,
          ),
          isFalse,
        );

        // Tap Continue
        final continueButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueButton);
        await tester.tap(continueButton);
        await tester.pumpAndSettle();

        // Preserved in controller
        expect(
          PurposeSelectionController.instance.selectedPurpose,
          PlatformPurpose.employmentVerification,
        );

        // Navigates to Screen 010 Onboarding Complete
        expect(find.byType(OnboardingCompleteScreen), findsOneWidget);
        expect(
          find.text(AppStrings.onboardingCompleteHeading),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Selecting Education Verification displays integration notice explaining direct automated verification is not active',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const PurposeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap Education Verification
        final educationCard = find.text(AppStrings.purposeEducationTitle);
        await tester.ensureVisible(educationCard);
        await tester.tap(educationCard);
        await tester.pumpAndSettle();

        // Integration notice displayed
        expect(find.text(AppStrings.integrationNoticeHeader), findsOneWidget);
        expect(
          find.text(AppStrings.educationIntegrationNotice),
          findsOneWidget,
        );

        // Verification capability safeguard
        expect(
          PurposeSelectionController.instance.isPurposeDirectlySupported(
            PlatformPurpose.educationVerification,
          ),
          isFalse,
        );
      },
    );

    testWidgets(
      'Selecting Organization Verification displays corporate registry authorization notice',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const PurposeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap Organization Verification
        final orgCard = find.text(AppStrings.purposeOrganizationTitle);
        await tester.ensureVisible(orgCard);
        await tester.tap(orgCard);
        await tester.pumpAndSettle();

        // Authorization notice displayed
        expect(find.text(AppStrings.integrationNoticeHeader), findsOneWidget);
        expect(
          find.text(AppStrings.organizationIntegrationNotice),
          findsOneWidget,
        );

        // Verification capability safeguard
        expect(
          PurposeSelectionController.instance.isPurposeDirectlySupported(
            PlatformPurpose.organizationVerification,
          ),
          isFalse,
        );
      },
    );

    testWidgets(
      'Selecting Digital Document Management and Other Purpose configures active workflows without integration warning',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const PurposeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap Digital Document Management
        final docsCard = find.text(AppStrings.purposeDigitalDocumentsTitle);
        await tester.ensureVisible(docsCard);
        await tester.tap(docsCard);
        await tester.pumpAndSettle();

        // No warning banner
        expect(find.text(AppStrings.integrationNoticeHeader), findsNothing);
        expect(
          PurposeSelectionController.instance.isPurposeDirectlySupported(
            PlatformPurpose.digitalDocumentManagement,
          ),
          isTrue,
        );

        // Tap Other Purpose
        final otherCard = find.text(AppStrings.purposeOtherTitle);
        await tester.ensureVisible(otherCard);
        await tester.tap(otherCard);
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.integrationNoticeHeader), findsNothing);
        expect(
          PurposeSelectionController.instance.isPurposeDirectlySupported(
            PlatformPurpose.otherPurpose,
          ),
          isTrue,
        );
      },
    );

    testWidgets(
      'Permission and verification safeguards: selecting a purpose never grants privileged access and never claims verification success',
      (WidgetTester tester) async {
        for (final purpose in PlatformPurpose.values) {
          PurposeSelectionController.instance.selectPurpose(purpose);
          expect(
            PurposeSelectionController.instance.hasPrivilegedAccess,
            isFalse,
          );
          expect(
            PurposeSelectionController.instance.claimsVerificationSuccess,
            isFalse,
          );
        }
      },
    );

    testWidgets(
      'Top back button returns to Screen 008 — User Type when opened from Screen 008',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const UserTypeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Select role on Screen 008 and proceed
        final indivTile = find.text(AppStrings.individualTitle);
        await tester.ensureVisible(indivTile);
        await tester.tap(indivTile);
        await tester.pumpAndSettle();

        final continueBtn = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueBtn);
        await tester.tap(continueBtn);
        await tester.pumpAndSettle();

        // Arrived at Screen 009
        expect(find.byType(PurposeSelectionScreen), findsOneWidget);

        // Tap top back button on Screen 009
        final backButton = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backButton);
        await tester.pumpAndSettle();

        // Returned cleanly to Screen 008
        expect(find.byType(UserTypeSelectionScreen), findsOneWidget);
        expect(find.text(AppStrings.userTypeHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Top back button replaces route to Screen 008 when opened standalone',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const PurposeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final backButton = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backButton);
        await tester.pumpAndSettle();

        // Replaced route to Screen 008
        expect(find.byType(UserTypeSelectionScreen), findsOneWidget);
        expect(find.text(AppStrings.userTypeHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Renders PurposeSelectionScreen without overflow on varied screen sizes',
      (WidgetTester tester) async {
        final screenSizes = [
          const Size(320, 568), // Small mobile (iPhone SE)
          const Size(390, 844), // Standard mobile (iPhone 13/14)
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const PurposeSelectionScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(
            find.text(AppStrings.purposeHeading),
            findsOneWidget,
          );
          expect(find.text(AppStrings.purposeIdentityTitle), findsOneWidget);
          expect(find.text(AppStrings.purposeEmploymentTitle), findsOneWidget);
          expect(find.text(AppStrings.purposeEducationTitle), findsOneWidget);
          expect(find.text(AppStrings.purposeOrganizationTitle), findsOneWidget);
          expect(find.text(AppStrings.purposeDigitalDocumentsTitle), findsOneWidget);
          expect(find.text(AppStrings.purposeOtherTitle), findsOneWidget);
          expect(find.text(AppStrings.continueAction), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons and purpose cards support keyboard navigation and focus on Screen 009',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const PurposeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(PurposeSelectionScreen), findsOneWidget);
      },
    );
  });

  group('Screen 010 — Onboarding Complete Screen Tests', () {
    setUp(() {
      LanguageController.instance.resetToDefault();
      LocationPreferencesController.instance.resetToDefault();
      UserTypeController.instance.resetToDefault();
      PurposeSelectionController.instance.resetToDefault();
      OnboardingStateController.instance.resetToDefault();
    });

    tearDown(() {
      LanguageController.instance.resetToDefault();
      LocationPreferencesController.instance.resetToDefault();
      UserTypeController.instance.resetToDefault();
      PurposeSelectionController.instance.resetToDefault();
      OnboardingStateController.instance.resetToDefault();
    });

    testWidgets(
      'Renders heading, supporting text, success shield illustration, summary card, disclaimer, and action buttons',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingCompleteScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Typography
        expect(find.text(AppStrings.onboardingCompleteHeading), findsOneWidget);
        expect(find.text(AppStrings.onboardingCompleteSupporting), findsOneWidget);

        // Visual Illustration & Top Back
        expect(find.byTooltip(AppStrings.backTooltip), findsOneWidget);
        expect(find.byType(OnboardingSuccessShieldVisual), findsOneWidget);
        expect(
          find.bySemanticsLabel(AppStrings.onboardingCompleteVisualSemantic),
          findsOneWidget,
        );

        // Summary Card
        expect(find.byType(OnboardingSummaryCard), findsOneWidget);
        expect(find.text(AppStrings.summarySectionHeader), findsOneWidget);

        // Disclaimer notice
        final disclaimerFinder = find.text(AppStrings.onboardingCompleteDisclaimer);
        await tester.ensureVisible(disclaimerFinder);
        expect(disclaimerFinder, findsOneWidget);

        // Action Buttons
        final createAccountButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.createAccountAction,
        );
        await tester.ensureVisible(createAccountButton);
        expect(createAccountButton, findsOneWidget);

        final signInButton = find.widgetWithText(
          OutlinedButton,
          AppStrings.alreadyHaveAccountAction,
        );
        await tester.ensureVisible(signInButton);
        expect(signInButton, findsOneWidget);
      },
    );

    testWidgets(
      'Displays populated selections in summary card when all selections are configured',
      (WidgetTester tester) async {
        // Configure preferences
        LanguageController.instance.setLanguage('ta');
        final india = LocationPreferencesController.instance.savedCountry!;
        final tn = india.regions.firstWhere((r) => r.code == 'TN');
        LocationPreferencesController.instance.saveLocation(india, tn);
        UserTypeController.instance.selectUserType(UserType.individual);
        PurposeSelectionController.instance.selectPurpose(
          PlatformPurpose.identityVerification,
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingCompleteScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Check configured values
        expect(find.text('Tamil — தமிழ்'), findsOneWidget);
        expect(find.text('India, Tamil Nadu'), findsOneWidget);
        expect(find.text(AppStrings.individualTitle), findsOneWidget);
        expect(find.text(AppStrings.purposeIdentityTitle), findsOneWidget);
      },
    );

    testWidgets(
      'Displays "Not configured" for missing selections and keeps summary honest without claiming completion',
      (WidgetTester tester) async {
        // Clear optional / required setup
        LocationPreferencesController.instance.clearSelection();
        UserTypeController.instance.clearSelection();
        PurposeSelectionController.instance.clearSelection();

        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingCompleteScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Language defaults to English
        expect(find.text('English'), findsOneWidget);

        // Location, UserType, and Purpose show as Not configured
        expect(find.text(AppStrings.summaryNotConfigured), findsNWidgets(3));

        // State controller confirms onboarding is NOT completed
        expect(OnboardingStateController.instance.isOnboardingCompleted, isFalse);
      },
    );

    testWidgets(
      'Tapping edit actions on summary card navigates to respective setup screens',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingCompleteScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Edit Language
        final editLanguage = find.byTooltip(
          '${AppStrings.summaryEditTooltip} (${AppStrings.summaryLanguageLabel})',
        );
        await tester.ensureVisible(editLanguage);
        await tester.tap(editLanguage);
        await tester.pumpAndSettle();

        expect(find.byType(LanguageSelectionScreen), findsOneWidget);

        // Pop back to Screen 010
        final backBtn = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backBtn);
        await tester.pumpAndSettle();

        expect(find.byType(OnboardingCompleteScreen), findsOneWidget);

        // Edit Country & Region
        final editLocation = find.byTooltip(
          '${AppStrings.summaryEditTooltip} (${AppStrings.summaryLocationLabel})',
        );
        await tester.ensureVisible(editLocation);
        await tester.tap(editLocation);
        await tester.pumpAndSettle();

        expect(find.byType(CountryRegionScreen), findsOneWidget);

        // Pop back
        await tester.tap(find.byTooltip(AppStrings.backTooltip));
        await tester.pumpAndSettle();

        expect(find.byType(OnboardingCompleteScreen), findsOneWidget);

        // Edit User Type
        final editUserType = find.byTooltip(
          '${AppStrings.summaryEditTooltip} (${AppStrings.summaryUserTypeLabel})',
        );
        await tester.ensureVisible(editUserType);
        await tester.tap(editUserType);
        await tester.pumpAndSettle();

        expect(find.byType(UserTypeSelectionScreen), findsOneWidget);

        // Pop back
        await tester.tap(find.byTooltip(AppStrings.backTooltip));
        await tester.pumpAndSettle();

        expect(find.byType(OnboardingCompleteScreen), findsOneWidget);

        // Edit Purpose
        final editPurpose = find.byTooltip(
          '${AppStrings.summaryEditTooltip} (${AppStrings.summaryPurposeLabel})',
        );
        await tester.ensureVisible(editPurpose);
        await tester.tap(editPurpose);
        await tester.pumpAndSettle();

        expect(find.byType(PurposeSelectionScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Validates required selections before completing onboarding and prevents Create Account if incomplete',
      (WidgetTester tester) async {
        // Missing user type and purpose
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingCompleteScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final createAccountButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.createAccountAction,
        );
        await tester.ensureVisible(createAccountButton);
        await tester.tap(createAccountButton);
        await tester.pumpAndSettle();

        // Validation error appears
        expect(
          find.byWidgetPredicate(
            (w) =>
                w is Text &&
                w.data != null &&
                w.data!.contains(AppStrings.onboardingIncompleteError),
          ),
          findsOneWidget,
        );

        // State remains incomplete and does NOT navigate
        expect(OnboardingStateController.instance.isOnboardingCompleted, isFalse);
        expect(find.byType(OnboardingCompleteScreen), findsOneWidget);
      },
    );

    testWidgets(
      '"Create Account" button marks onboarding completed and navigates to Screen 011 — Create Account',
      (WidgetTester tester) async {
        // Setup valid required selections
        final india = LocationPreferencesController.instance.savedCountry!;
        final tn = india.regions.firstWhere((r) => r.code == 'TN');
        LocationPreferencesController.instance.saveLocation(india, tn);
        UserTypeController.instance.selectUserType(UserType.individual);
        PurposeSelectionController.instance.selectPurpose(
          PlatformPurpose.identityVerification,
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingCompleteScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final createAccountButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.createAccountAction,
        );
        await tester.ensureVisible(createAccountButton);
        await tester.tap(createAccountButton);
        await tester.pumpAndSettle();

        // Marked as completed in state controller
        expect(OnboardingStateController.instance.isOnboardingCompleted, isTrue);

        // Navigated to Screen 011 Create Account screen
        expect(find.byType(CreateAccountScreen), findsOneWidget);
        expect(
          find.text(AppStrings.createAccountHeading),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      '"Already Have an Account? Sign In" button navigates to existing Screen Sign In route',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingCompleteScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final signInButton = find.widgetWithText(
          OutlinedButton,
          AppStrings.alreadyHaveAccountAction,
        );
        await tester.ensureVisible(signInButton);
        await tester.tap(signInButton);
        await tester.pumpAndSettle();

        // Navigated to existing Sign In route (LoginScreen)
        expect(find.byType(LoginScreen), findsOneWidget);
        expect(find.text(AppStrings.loginHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Security & verification safeguards: onboarding completion never creates authenticated session or claims identity verification',
      (WidgetTester tester) async {
        final india = LocationPreferencesController.instance.savedCountry!;
        final tn = india.regions.firstWhere((r) => r.code == 'TN');
        LocationPreferencesController.instance.saveLocation(india, tn);
        UserTypeController.instance.selectUserType(UserType.individual);
        PurposeSelectionController.instance.selectPurpose(
          PlatformPurpose.identityVerification,
        );

        // Mark completed
        final success = OnboardingStateController.instance.markOnboardingCompleted();
        expect(success, isTrue);
        expect(OnboardingStateController.instance.isOnboardingCompleted, isTrue);

        // Safeguards
        expect(
          OnboardingStateController.instance.hasAuthenticatedSession,
          isFalse,
        );
        expect(
          OnboardingStateController.instance.isIdentityVerified,
          isFalse,
        );
        expect(
          OnboardingStateController.instance.hasPrivilegedAccess,
          isFalse,
        );
      },
    );

    testWidgets(
      'Top back button returns to Screen 009 — Purpose Selection when opened from Screen 009',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const PurposeSelectionScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Select purpose and proceed to Screen 010
        final identityCard = find.text(AppStrings.purposeIdentityTitle);
        await tester.ensureVisible(identityCard);
        await tester.tap(identityCard);
        await tester.pumpAndSettle();

        final continueBtn = find.widgetWithText(
          ElevatedButton,
          AppStrings.continueAction,
        );
        await tester.ensureVisible(continueBtn);
        await tester.tap(continueBtn);
        await tester.pumpAndSettle();

        // Arrived at Screen 010
        expect(find.byType(OnboardingCompleteScreen), findsOneWidget);

        // Tap top back button on Screen 010
        final backButton = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backButton);
        await tester.pumpAndSettle();

        // Returned cleanly to Screen 009
        expect(find.byType(PurposeSelectionScreen), findsOneWidget);
        expect(find.text(AppStrings.purposeHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Top back button replaces route to Screen 009 when opened standalone',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingCompleteScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final backButton = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backButton);
        await tester.pumpAndSettle();

        // Replaced route to Screen 009
        expect(find.byType(PurposeSelectionScreen), findsOneWidget);
        expect(find.text(AppStrings.purposeHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Renders OnboardingCompleteScreen without overflow across multiple device screen sizes',
      (WidgetTester tester) async {
        final screenSizes = [
          const Size(320, 568), // Small mobile (iPhone SE)
          const Size(390, 844), // Standard mobile (iPhone 13/14)
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const OnboardingCompleteScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(
            find.text(AppStrings.onboardingCompleteHeading),
            findsOneWidget,
          );
          expect(find.byType(OnboardingSummaryCard), findsOneWidget);
          expect(find.text(AppStrings.createAccountAction), findsOneWidget);
          expect(find.text(AppStrings.alreadyHaveAccountAction), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons, summary items, and back button support keyboard navigation and focus on Screen 010',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingCompleteScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(OnboardingCompleteScreen), findsOneWidget);
      },
    );
  });

  group('Screen 011 — Create Account Screen Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
    });

    tearDown(() {
      AuthService.instance.resetToDefault();
    });

    testWidgets(
      'Renders all registration elements: heading, subtitle, fields, checklist, checkbox, and buttons',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CreateAccountScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Typography & Emblem
        expect(find.text(AppStrings.createAccountHeading), findsOneWidget);
        expect(find.text(AppStrings.createAccountSubtitle), findsOneWidget);
        expect(find.byTooltip(AppStrings.backTooltip), findsOneWidget);

        // Form Fields
        expect(find.text(AppStrings.fullNameLabel), findsOneWidget);
        expect(find.text(AppStrings.emailLabel), findsOneWidget);
        expect(find.text(AppStrings.passwordLabel), findsOneWidget);
        expect(find.text(AppStrings.confirmPasswordLabel), findsOneWidget);

        // Password Requirements Checklist
        expect(find.text(AppStrings.passwordPolicyHeader), findsOneWidget);
        expect(find.text(AppStrings.passwordPolicyLength), findsOneWidget);
        expect(find.text(AppStrings.passwordPolicyUppercase), findsOneWidget);
        expect(find.text(AppStrings.passwordPolicyLowercase), findsOneWidget);
        expect(find.text(AppStrings.passwordPolicyNumber), findsOneWidget);

        // Terms Checkbox & Policy Links
        final checkbox = find.byType(Checkbox);
        await tester.ensureVisible(checkbox);
        expect(checkbox, findsOneWidget);
        expect(
          find.textContaining(AppStrings.termsOfServiceLink, findRichText: true),
          findsOneWidget,
        );

        // Buttons
        final submitButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.createAccountSubmitButton,
        );
        await tester.ensureVisible(submitButton);
        expect(submitButton, findsOneWidget);

        expect(find.text(AppStrings.alreadyHaveAccountLink), findsOneWidget);
      },
    );

    testWidgets(
      'Toggles password and confirm password visibility correctly',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CreateAccountScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Toggle password visibility
        final showPassBtn = find.byTooltip('Show password');
        expect(showPassBtn, findsOneWidget);
        await tester.tap(showPassBtn);
        await tester.pumpAndSettle();

        expect(find.byTooltip('Hide password'), findsOneWidget);

        // Toggle confirm password visibility
        final showConfirmBtn = find.byTooltip('Show confirm password');
        await tester.ensureVisible(showConfirmBtn);
        expect(showConfirmBtn, findsOneWidget);
        await tester.tap(showConfirmBtn);
        await tester.pumpAndSettle();

        expect(find.byTooltip('Hide confirm password'), findsOneWidget);
      },
    );

    testWidgets(
      'Updates password requirement checklist in real time as password changes',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CreateAccountScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final passField = find.byKey(const Key('passwordField'));

        // Enter partial password 'pass'
        await tester.enterText(passField, 'pass');
        await tester.pumpAndSettle();

        // Lowercase met, but length, upper, digit not met
        expect(
          find.byWidgetPredicate(
            (w) =>
                w is PasswordRequirementItem &&
                w.label == AppStrings.passwordPolicyLowercase &&
                w.isMet,
          ),
          findsOneWidget,
        );
        expect(
          find.byWidgetPredicate(
            (w) =>
                w is PasswordRequirementItem &&
                w.label == AppStrings.passwordPolicyLength &&
                !w.isMet,
          ),
          findsOneWidget,
        );

        // Enter complete strong password 'Passw0rd123'
        await tester.enterText(passField, 'Passw0rd123');
        await tester.pumpAndSettle();

        expect(
          find.byWidgetPredicate(
            (w) =>
                w is PasswordRequirementItem &&
                w.label == AppStrings.passwordPolicyLength &&
                w.isMet,
          ),
          findsOneWidget,
        );
        expect(
          find.byWidgetPredicate(
            (w) =>
                w is PasswordRequirementItem &&
                w.label == AppStrings.passwordPolicyUppercase &&
                w.isMet,
          ),
          findsOneWidget,
        );
        expect(
          find.byWidgetPredicate(
            (w) =>
                w is PasswordRequirementItem &&
                w.label == AppStrings.passwordPolicyLowercase &&
                w.isMet,
          ),
          findsOneWidget,
        );
        expect(
          find.byWidgetPredicate(
            (w) =>
                w is PasswordRequirementItem &&
                w.label == AppStrings.passwordPolicyNumber &&
                w.isMet,
          ),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Validation: shows field-specific error for empty full name',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CreateAccountScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap submit without typing anything
        final submitButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.createAccountSubmitButton,
        );
        await tester.ensureVisible(submitButton);
        await tester.tap(submitButton);
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.fullNameRequiredError), findsOneWidget);
      },
    );

    testWidgets(
      'Validation: shows field-specific error for invalid email formats',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CreateAccountScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final nameField = find.byKey(const Key('fullNameField'));
        final emailField = find.byKey(const Key('emailField'));

        await tester.enterText(nameField, 'Alex Morgan');
        await tester.enterText(emailField, 'invalid-email');
        await tester.pumpAndSettle();

        final submitButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.createAccountSubmitButton,
        );
        await tester.ensureVisible(submitButton);
        await tester.tap(submitButton);
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.emailInvalidError), findsOneWidget);
      },
    );

    testWidgets(
      'Validation: shows field-specific error when password does not meet complexity requirements',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CreateAccountScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final nameField = find.byKey(const Key('fullNameField'));
        final emailField = find.byKey(const Key('emailField'));
        final passField = find.byKey(const Key('passwordField'));

        await tester.enterText(nameField, 'Alex Morgan');
        await tester.enterText(emailField, 'alex@example.com');
        await tester.enterText(passField, 'weak');
        await tester.pumpAndSettle();

        final submitButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.createAccountSubmitButton,
        );
        await tester.ensureVisible(submitButton);
        await tester.tap(submitButton);
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.passwordPolicyNotMetError), findsOneWidget);
      },
    );

    testWidgets(
      'Validation: shows field-specific error when confirm password does not match',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CreateAccountScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final nameField = find.byKey(const Key('fullNameField'));
        final emailField = find.byKey(const Key('emailField'));
        final passField = find.byKey(const Key('passwordField'));
        final confirmField = find.byKey(const Key('confirmPasswordField'));

        await tester.enterText(nameField, 'Alex Morgan');
        await tester.enterText(emailField, 'alex@example.com');
        await tester.enterText(passField, 'Passw0rd123');
        await tester.enterText(confirmField, 'Different123');
        await tester.pumpAndSettle();

        final submitButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.createAccountSubmitButton,
        );
        await tester.ensureVisible(submitButton);
        await tester.tap(submitButton);
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.passwordsDoNotMatchError), findsOneWidget);
      },
    );

    testWidgets(
      'Validation: shows field-specific error when terms and privacy checkbox is unchecked',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CreateAccountScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final nameField = find.byKey(const Key('fullNameField'));
        final emailField = find.byKey(const Key('emailField'));
        final passField = find.byKey(const Key('passwordField'));
        final confirmField = find.byKey(const Key('confirmPasswordField'));

        await tester.enterText(nameField, 'Alex Morgan');
        await tester.enterText(emailField, 'alex@example.com');
        await tester.enterText(passField, 'Passw0rd123');
        await tester.enterText(confirmField, 'Passw0rd123');
        await tester.pumpAndSettle();

        final submitButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.createAccountSubmitButton,
        );
        await tester.ensureVisible(submitButton);
        await tester.tap(submitButton);
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.termsRequiredError), findsOneWidget);

        // Checking the terms clears the error
        final checkbox = find.byType(Checkbox);
        await tester.ensureVisible(checkbox);
        await tester.tap(checkbox);
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.termsRequiredError), findsNothing);
      },
    );

    testWidgets(
      'Tapping terms of service link opens terms and privacy policy dialog',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CreateAccountScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final termsRichText = find.byWidgetPredicate(
          (w) =>
              w is RichText &&
              w.text.toPlainText().contains(AppStrings.termsOfServiceLink),
        );
        await tester.ensureVisible(termsRichText);

        // Tap on Terms of Service span
        final richTextWidget = tester.widget<RichText>(termsRichText);
        TapGestureRecognizer? recognizer;
        richTextWidget.text.visitChildren((span) {
          if (span is TextSpan && span.recognizer is TapGestureRecognizer) {
            recognizer = span.recognizer as TapGestureRecognizer;
            return false;
          }
          return true;
        });
        expect(recognizer, isNotNull);
        recognizer!.onTap!();
        await tester.pumpAndSettle();

        // Verify Dialog
        expect(find.text(AppStrings.termsDialogTitle), findsOneWidget);
        expect(find.text(AppStrings.termsDialogContent), findsOneWidget);

        // Close Dialog
        await tester.tap(find.text(AppStrings.closeAction));
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.termsDialogTitle), findsNothing);
      },
    );

    testWidgets(
      'Handles authentication errors (existing account) and displays error banner without crashing',
      (WidgetTester tester) async {
        // Setup mock failure delegate
        AuthService.instance.setSignUpDelegate(({
          required String fullName,
          required String email,
          required String password,
        }) async {
          return AuthRegistrationResult.failure(
            errorMessage: AppStrings.authErrorUserAlreadyExists,
            errorCode: AuthErrorCode.userAlreadyExists,
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const CreateAccountScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final nameField = find.byKey(const Key('fullNameField'));
        final emailField = find.byKey(const Key('emailField'));
        final passField = find.byKey(const Key('passwordField'));
        final confirmField = find.byKey(const Key('confirmPasswordField'));

        await tester.enterText(nameField, 'Alex Morgan');
        await tester.enterText(emailField, 'alex@example.com');
        await tester.enterText(passField, 'Passw0rd123');
        await tester.enterText(confirmField, 'Passw0rd123');

        final checkbox = find.byType(Checkbox);
        await tester.ensureVisible(checkbox);
        await tester.tap(checkbox);
        await tester.pumpAndSettle();

        final submitButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.createAccountSubmitButton,
        );
        await tester.ensureVisible(submitButton);
        await tester.tap(submitButton);
        await tester.pumpAndSettle();

        // Error banner is displayed
        expect(find.text(AppStrings.authErrorUserAlreadyExists), findsOneWidget);
        expect(find.byIcon(Icons.error_outline_rounded), findsOneWidget);
      },
    );

    testWidgets(
      'Handles network error and rate limit gracefully without exposing internal secrets',
      (WidgetTester tester) async {
        AuthService.instance.setSignUpDelegate(({
          required String fullName,
          required String email,
          required String password,
        }) async {
          return AuthRegistrationResult.failure(
            errorMessage: AppStrings.authErrorNetwork,
            errorCode: AuthErrorCode.networkError,
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const CreateAccountScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final nameField = find.byKey(const Key('fullNameField'));
        final emailField = find.byKey(const Key('emailField'));
        final passField = find.byKey(const Key('passwordField'));
        final confirmField = find.byKey(const Key('confirmPasswordField'));

        await tester.enterText(nameField, 'Alex Morgan');
        await tester.enterText(emailField, 'alex@example.com');
        await tester.enterText(passField, 'Passw0rd123');
        await tester.enterText(confirmField, 'Passw0rd123');

        final checkbox = find.byType(Checkbox);
        await tester.ensureVisible(checkbox);
        await tester.tap(checkbox);
        await tester.pumpAndSettle();

        final submitButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.createAccountSubmitButton,
        );
        await tester.ensureVisible(submitButton);
        await tester.tap(submitButton);
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.authErrorNetwork), findsOneWidget);
      },
    );

    testWidgets(
      'Successful registration displays confirmation notification and navigates to Screen 012 — Email Verification',
      (WidgetTester tester) async {
        AuthService.instance.setSignUpDelegate(({
          required String fullName,
          required String email,
          required String password,
        }) async {
          return AuthRegistrationResult.success(
            email: email,
            requiresEmailConfirmation: true,
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const CreateAccountScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final nameField = find.byKey(const Key('fullNameField'));
        final emailField = find.byKey(const Key('emailField'));
        final passField = find.byKey(const Key('passwordField'));
        final confirmField = find.byKey(const Key('confirmPasswordField'));

        await tester.enterText(nameField, 'Alex Morgan');
        await tester.enterText(emailField, 'alex@example.com');
        await tester.enterText(passField, 'Passw0rd123');
        await tester.enterText(confirmField, 'Passw0rd123');

        final checkbox = find.byType(Checkbox);
        await tester.ensureVisible(checkbox);
        await tester.tap(checkbox);
        await tester.pumpAndSettle();

        final submitButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.createAccountSubmitButton,
        );
        await tester.ensureVisible(submitButton);
        await tester.tap(submitButton);
        await tester.pumpAndSettle();

        // Navigated to Screen 013 Email Verification
        expect(find.byType(EmailVerificationScreen), findsOneWidget);
        expect(
          find.text(AppStrings.emailVerificationHeading),
          findsOneWidget,
        );
        expect(find.text('alex@example.com'), findsOneWidget);
      },
    );

    testWidgets(
      'Secondary link "Already have an account? Sign In" navigates to AppRoutes.signIn',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CreateAccountScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final signInLink = find.text(AppStrings.alreadyHaveAccountLink);
        await tester.ensureVisible(signInLink);
        await tester.tap(signInLink);
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
        expect(find.text(AppStrings.loginHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Top back button returns to Screen 010 — Onboarding Complete',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const OnboardingCompleteScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Configure required preferences to allow proceeding
        final india = LocationPreferencesController.instance.savedCountry!;
        final tn = india.regions.firstWhere((r) => r.code == 'TN');
        LocationPreferencesController.instance.saveLocation(india, tn);
        UserTypeController.instance.selectUserType(UserType.individual);
        PurposeSelectionController.instance.selectPurpose(
          PlatformPurpose.identityVerification,
        );

        final createAccountButton = find.widgetWithText(
          ElevatedButton,
          AppStrings.createAccountAction,
        );
        await tester.ensureVisible(createAccountButton);
        await tester.tap(createAccountButton);
        await tester.pumpAndSettle();

        // Arrived at Screen 011
        expect(find.byType(CreateAccountScreen), findsOneWidget);

        // Tap top back button
        final backButton = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backButton);
        await tester.pumpAndSettle();

        // Returned cleanly to Screen 010
        expect(find.byType(OnboardingCompleteScreen), findsOneWidget);
        expect(find.text(AppStrings.onboardingCompleteHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Renders CreateAccountScreen without overflow across multiple device screen sizes',
      (WidgetTester tester) async {
        final screenSizes = [
          const Size(320, 568), // Small mobile (iPhone SE)
          const Size(390, 844), // Standard mobile (iPhone 13/14)
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const CreateAccountScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(
            find.text(AppStrings.createAccountHeading),
            findsOneWidget,
          );
          expect(find.text(AppStrings.fullNameLabel), findsOneWidget);
          expect(find.text(AppStrings.emailLabel), findsOneWidget);
          expect(find.text(AppStrings.passwordLabel), findsOneWidget);
          expect(find.text(AppStrings.createAccountSubmitButton), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons, form fields, and checkbox support keyboard navigation and focus on Screen 011',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const CreateAccountScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(CreateAccountScreen), findsOneWidget);
      },
    );
  });

  group('Screen 012 — Login Screen Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
    });

    tearDown(() {
      AuthService.instance.resetToDefault();
    });

    testWidgets(
      'Renders all login elements: logo, heading, subtitle, fields, remember me, forgot password, and sign in button',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Heading & Subtitle
        expect(find.text(AppStrings.loginHeading), findsOneWidget);
        expect(find.text(AppStrings.loginSubtitle), findsOneWidget);

        // Logo
        expect(find.byType(IdentityTrustLogo), findsOneWidget);

        // Back button
        expect(find.byTooltip(AppStrings.backTooltip), findsOneWidget);

        // Fields
        expect(find.text(AppStrings.emailLabel), findsOneWidget);
        expect(find.byKey(const Key('loginEmailField')), findsOneWidget);
        expect(find.text(AppStrings.passwordLabel), findsOneWidget);
        expect(find.byKey(const Key('loginPasswordField')), findsOneWidget);

        // Remember me & Forgot Password
        expect(find.byKey(const Key('rememberMeCheckbox')), findsOneWidget);
        expect(find.text(AppStrings.rememberMeLabel), findsOneWidget);
        expect(find.byKey(const Key('forgotPasswordLink')), findsOneWidget);
        expect(find.text(AppStrings.forgotPasswordLink), findsOneWidget);

        // Buttons
        expect(find.byKey(const Key('loginSubmitButton')), findsOneWidget);
        expect(find.text(AppStrings.signInSubmitButton), findsOneWidget);

        // Create Account link
        expect(find.byKey(const Key('createAccountLink')), findsOneWidget);
      },
    );

    testWidgets(
      'Toggles password visibility obscureText correctly using show/hide button',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Initially obscured
        final showBtn = find.byTooltip('Show password');
        expect(showBtn, findsOneWidget);

        // Tap toggle
        await tester.tap(showBtn);
        await tester.pumpAndSettle();

        // Now revealed
        expect(find.byTooltip('Hide password'), findsOneWidget);

        // Tap again to hide
        await tester.tap(find.byTooltip('Hide password'));
        await tester.pumpAndSettle();

        expect(find.byTooltip('Show password'), findsOneWidget);
      },
    );

    testWidgets(
      'Remember me checkbox toggles state safely',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final checkbox = tester.widget<Checkbox>(
          find.byKey(const Key('rememberMeCheckbox')),
        );
        expect(checkbox.value, isTrue);

        // Tap checkbox to uncheck
        await tester.tap(find.byKey(const Key('rememberMeCheckbox')));
        await tester.pumpAndSettle();

        final updatedCheckbox = tester.widget<Checkbox>(
          find.byKey(const Key('rememberMeCheckbox')),
        );
        expect(updatedCheckbox.value, isFalse);
      },
    );

    testWidgets(
      'Validation: shows field-specific error for empty email',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap Sign In without filling form
        await tester.tap(find.byKey(const Key('loginSubmitButton')));
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.emailRequiredError), findsOneWidget);
      },
    );

    testWidgets(
      'Validation: shows field-specific error for invalid email format',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('loginEmailField')),
          'not-an-email',
        );
        await tester.enterText(
          find.byKey(const Key('loginPasswordField')),
          'Secret1234',
        );

        await tester.tap(find.byKey(const Key('loginSubmitButton')));
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.emailInvalidError), findsOneWidget);
      },
    );

    testWidgets(
      'Validation: shows field-specific error for empty password',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('loginEmailField')),
          'alex@example.com',
        );

        await tester.tap(find.byKey(const Key('loginSubmitButton')));
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.passwordRequiredError), findsOneWidget);
      },
    );

    testWidgets(
      'Handles invalid credentials and displays understandable error banner without leaking whether account exists',
      (WidgetTester tester) async {
        AuthService.instance.setSignInDelegate(({
          required String email,
          required String password,
        }) async {
          return AuthSignInResult.failure(
            errorMessage: AppStrings.authErrorInvalidCredentials,
            errorCode: AuthErrorCode.invalidCredentials,
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('loginEmailField')),
          'alex@example.com',
        );
        await tester.enterText(
          find.byKey(const Key('loginPasswordField')),
          'WrongPassword1',
        );

        await tester.tap(find.byKey(const Key('loginSubmitButton')));
        await tester.pumpAndSettle();

        // Error banner is visible
        expect(find.text(AppStrings.authErrorInvalidCredentials), findsOneWidget);
        expect(find.byIcon(Icons.error_outline_rounded), findsOneWidget);
        expect(AuthService.instance.hasAuthenticatedSession, isFalse);
      },
    );

    testWidgets(
      'Handles unverified email error and navigates to Screen 012 — Email Verification flow',
      (WidgetTester tester) async {
        AuthService.instance.setSignInDelegate(({
          required String email,
          required String password,
        }) async {
          return AuthSignInResult.requiresConfirmation(
            email: email,
            errorMessage: AppStrings.authErrorEmailNotConfirmed,
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('loginEmailField')),
          'alex@example.com',
        );
        await tester.enterText(
          find.byKey(const Key('loginPasswordField')),
          'CorrectPass123',
        );

        await tester.tap(find.byKey(const Key('loginSubmitButton')));
        await tester.pumpAndSettle();

        // Navigates to email verification route
        expect(find.byType(EmailVerificationScreen), findsOneWidget);
        expect(
          find.text(AppStrings.emailVerificationHeading),
          findsOneWidget,
        );
        expect(find.text('alex@example.com'), findsOneWidget);
        expect(AuthService.instance.hasAuthenticatedSession, isFalse);
      },
    );

    testWidgets(
      'Handles network error and rate limit gracefully without exposing internal secrets',
      (WidgetTester tester) async {
        AuthService.instance.setSignInDelegate(({
          required String email,
          required String password,
        }) async {
          return AuthSignInResult.failure(
            errorMessage: AppStrings.authErrorNetwork,
            errorCode: AuthErrorCode.networkError,
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('loginEmailField')),
          'alex@example.com',
        );
        await tester.enterText(
          find.byKey(const Key('loginPasswordField')),
          'CorrectPass123',
        );

        await tester.tap(find.byKey(const Key('loginSubmitButton')));
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.authErrorNetwork), findsOneWidget);
        expect(AuthService.instance.hasAuthenticatedSession, isFalse);
      },
    );

    testWidgets(
      'Successful login creates authenticated session, displays confirmation toast, and navigates to authorized workspace route',
      (WidgetTester tester) async {
        AuthService.instance.setSignInDelegate(({
          required String email,
          required String password,
        }) async {
          return AuthSignInResult.success(
            email: email,
            userId: 'usr_valid_123',
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('loginEmailField')),
          'alex.morgan@trustplatform.ai',
        );
        await tester.enterText(
          find.byKey(const Key('loginPasswordField')),
          'Passw0rd123',
        );

        await tester.tap(find.byKey(const Key('loginSubmitButton')));
        await tester.pumpAndSettle();

        // Active session established
        expect(AuthService.instance.hasAuthenticatedSession, isTrue);
        expect(
          AuthService.instance.currentUserEmail,
          'alex.morgan@trustplatform.ai',
        );

        // Navigates to authorized workspace landing route
        expect(find.byType(RoutePlaceholderScreen), findsOneWidget);
        expect(
          find.text(AppStrings.workspacePlaceholderTitle),
          findsNWidgets(2),
        );
      },
    );

    testWidgets(
      'Tapping "Forgot Password?" link navigates to password recovery route',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final forgotBtn = find.byKey(const Key('forgotPasswordLink'));
        await tester.ensureVisible(forgotBtn);
        await tester.tap(forgotBtn);
        await tester.pumpAndSettle();

        // Navigates to Screen 015 — Forgot Password route
        expect(find.byType(ForgotPasswordScreen), findsOneWidget);
        expect(
          find.text(AppStrings.forgotPasswordHeading),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Tapping "Don\'t have an account? Create Account" link navigates to Screen 011 — Create Account',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final createAccountLink = find.byKey(const Key('createAccountLink'));
        await tester.ensureVisible(createAccountLink);
        await tester.tap(createAccountLink);
        await tester.pumpAndSettle();

        // Arrived at Screen 011
        expect(find.byType(CreateAccountScreen), findsOneWidget);
        expect(find.text(AppStrings.createAccountHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Top back button returns to Welcome screen when opened from Welcome',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const WelcomeScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final signInButton = find.text(AppStrings.signIn);
        await tester.ensureVisible(signInButton);
        await tester.tap(signInButton);
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);

        // Tap top back button
        final backButton = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backButton);
        await tester.pumpAndSettle();

        // Returned cleanly to WelcomeScreen
        expect(find.byType(WelcomeScreen), findsOneWidget);
        expect(find.text(AppStrings.welcomeHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Submitting form disables primary button and shows loading spinner during authentication in flight',
      (WidgetTester tester) async {
        final completer = Completer<AuthSignInResult>();
        AuthService.instance.setSignInDelegate(({
          required String email,
          required String password,
        }) {
          return completer.future;
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('loginEmailField')),
          'alex@example.com',
        );
        await tester.enterText(
          find.byKey(const Key('loginPasswordField')),
          'Secret123',
        );

        await tester.tap(find.byKey(const Key('loginSubmitButton')));
        await tester.pump(); // Start frame of submission

        // Button shows loading spinner
        expect(find.byType(CircularProgressIndicator), findsOneWidget);

        // Complete the future
        completer.complete(
          AuthSignInResult.success(email: 'alex@example.com'),
        );
        await tester.pumpAndSettle();

        expect(find.byType(CircularProgressIndicator), findsNothing);
      },
    );

    testWidgets(
      'Renders LoginScreen without overflow across multiple device screen sizes',
      (WidgetTester tester) async {
        final screenSizes = [
          const Size(320, 568), // Small mobile (iPhone SE)
          const Size(390, 844), // Standard mobile (iPhone 13/14)
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const LoginScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.text(AppStrings.loginHeading), findsOneWidget);
          expect(find.byKey(const Key('loginEmailField')), findsOneWidget);
          expect(find.byKey(const Key('loginPasswordField')), findsOneWidget);
          expect(find.byKey(const Key('loginSubmitButton')), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons, form fields, checkbox, and links support keyboard navigation and focus on Screen 012',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );
  });

  group('Screen 013 — Email Verification Screen Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
    });

    tearDown(() {
      AuthService.instance.resetToDefault();
    });

    testWidgets(
      'Renders all email verification elements: logo, heading, subtitle, target email badge, instructions card, buttons, and back to sign in link',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const EmailVerificationScreen(email: 'alex@example.com'),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Heading & Subtitle
        expect(find.text(AppStrings.emailVerificationHeading), findsOneWidget);
        expect(find.text(AppStrings.emailVerificationSubtitle), findsOneWidget);

        // Logo
        expect(find.byType(IdentityTrustLogo), findsOneWidget);

        // Top back button
        expect(find.byTooltip(AppStrings.backTooltip), findsOneWidget);

        // Target Email Badge
        expect(
          find.text(AppStrings.emailVerificationTargetPrefix),
          findsOneWidget,
        );
        expect(find.text('alex@example.com'), findsOneWidget);

        // Instructions Card
        expect(find.text(AppStrings.emailVerificationStep1), findsOneWidget);
        expect(find.text(AppStrings.emailVerificationStep2), findsOneWidget);
        expect(find.text(AppStrings.emailVerificationStep3), findsOneWidget);

        // Buttons
        expect(
          find.byKey(const Key('checkVerificationStatusButton')),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.emailVerificationCheckStatusButton),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('resendVerificationButton')),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.emailVerificationResendButton),
          findsOneWidget,
        );

        // Help Note & Back to Sign In Link
        expect(
          find.text(AppStrings.emailVerificationCheckSpamNote),
          findsOneWidget,
        );
        expect(find.byKey(const Key('backToSignInLink')), findsOneWidget);
        expect(
          find.text(AppStrings.emailVerificationBackToLogin),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Displays email provided via route settings arguments Map',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Builder(
              builder: (context) => Scaffold(
                body: ElevatedButton(
                  onPressed: () {
                    Navigator.of(context).pushNamed(
                      AppRoutes.emailVerification,
                      arguments: {'email': 'taylor@domain.org'},
                    );
                  },
                  child: const Text('Open Verification'),
                ),
              ),
            ),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.tap(find.text('Open Verification'));
        await tester.pumpAndSettle();

        expect(find.byType(EmailVerificationScreen), findsOneWidget);
        expect(find.text('taylor@domain.org'), findsOneWidget);
      },
    );

    testWidgets(
      'Falls back safely to default notice when email is omitted',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const EmailVerificationScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.emailVerificationFallbackEmail),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Displays loading indicator while verification status check is in flight',
      (WidgetTester tester) async {
        final completer = Completer<AuthVerificationResult>();
        AuthService.instance.setCheckVerificationDelegate(({
          required String email,
        }) {
          return completer.future;
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const EmailVerificationScreen(email: 'alex@example.com'),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final checkBtn = find.byKey(const Key('checkVerificationStatusButton'));
        await tester.ensureVisible(checkBtn);
        await tester.tap(checkBtn);
        await tester.pump(); // Start frame

        // Spinner displayed
        expect(find.byType(CircularProgressIndicator), findsOneWidget);

        completer.complete(
          AuthVerificationResult.pending(email: 'alex@example.com'),
        );
        await tester.pumpAndSettle();

        expect(find.byType(CircularProgressIndicator), findsNothing);
      },
    );

    testWidgets(
      'Shows informative pending banner when confirmation is still pending without granting session or fabricating success',
      (WidgetTester tester) async {
        AuthService.instance.setCheckVerificationDelegate(({
          required String email,
        }) async {
          return AuthVerificationResult.pending(
            email: email,
            message: AppStrings.emailVerificationPendingBanner,
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const EmailVerificationScreen(email: 'alex@example.com'),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final checkBtn = find.byKey(const Key('checkVerificationStatusButton'));
        await tester.ensureVisible(checkBtn);
        await tester.tap(checkBtn);
        await tester.pumpAndSettle();

        // Informative pending banner is displayed
        expect(find.byKey(const Key('verificationInfoBanner')), findsOneWidget);
        expect(
          find.text(AppStrings.emailVerificationPendingBanner),
          findsOneWidget,
        );

        // Security safeguard: Session is NOT established
        expect(AuthService.instance.hasAuthenticatedSession, isFalse);
      },
    );

    testWidgets(
      'Successful verification check creates authenticated session, displays toast, and navigates to authorized workspace route',
      (WidgetTester tester) async {
        AuthService.instance.setCheckVerificationDelegate(({
          required String email,
        }) async {
          return AuthVerificationResult.verified(email: email);
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const EmailVerificationScreen(email: 'alex@example.com'),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final checkBtn = find.byKey(const Key('checkVerificationStatusButton'));
        await tester.ensureVisible(checkBtn);
        await tester.tap(checkBtn);
        await tester.pumpAndSettle();

        // Navigates to workspace route
        expect(find.byType(RoutePlaceholderScreen), findsOneWidget);
        expect(
          find.text(AppStrings.workspacePlaceholderTitle),
          findsNWidgets(2),
        );

        // Security safeguard: Real session is established
        expect(AuthService.instance.hasAuthenticatedSession, isTrue);
        expect(AuthService.instance.currentUserEmail, 'alex@example.com');
      },
    );

    testWidgets(
      'Resend button triggers resend email, displays success snackbar, and activates cooldown countdown',
      (WidgetTester tester) async {
        bool resendCalled = false;
        AuthService.instance.setResendDelegate(({
          required String email,
        }) async {
          resendCalled = true;
          return AuthResendResult.success(cooldownSeconds: 60);
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const EmailVerificationScreen(email: 'alex@example.com'),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final resendBtn = find.byKey(const Key('resendVerificationButton'));
        await tester.ensureVisible(resendBtn);
        await tester.tap(resendBtn);
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 300));

        expect(resendCalled, isTrue);
        expect(
          find.text(AppStrings.emailVerificationResendSuccess),
          findsAtLeastNWidgets(1),
        );

        // Button now displays cooldown countdown and is disabled
        expect(
          find.textContaining(AppStrings.emailVerificationResendCooldownPrefix),
          findsOneWidget,
        );

        // Clean up active timer by pumping replacement widget
        await tester.pumpWidget(const SizedBox());
      },
    );

    testWidgets(
      'Handles resend failure gracefully with accessible error banner without crashing',
      (WidgetTester tester) async {
        AuthService.instance.setResendDelegate(({
          required String email,
        }) async {
          return AuthResendResult.failure(
            errorMessage: AppStrings.authErrorRateLimit,
            errorCode: AuthErrorCode.rateLimitExceeded,
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const EmailVerificationScreen(email: 'alex@example.com'),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final resendBtn = find.byKey(const Key('resendVerificationButton'));
        await tester.ensureVisible(resendBtn);
        await tester.tap(resendBtn);
        await tester.pumpAndSettle();

        // Error banner is visible
        expect(find.byKey(const Key('verificationErrorBanner')), findsOneWidget);
        expect(find.text(AppStrings.authErrorRateLimit), findsOneWidget);
      },
    );

    testWidgets(
      'Tapping "Back to Sign In" navigates back to LoginScreen route',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const EmailVerificationScreen(email: 'alex@example.com'),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final backLink = find.byKey(const Key('backToSignInLink'));
        await tester.ensureVisible(backLink);
        await tester.tap(backLink);
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
        expect(find.text(AppStrings.loginHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Top back button returns to Welcome screen when opened standalone',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const EmailVerificationScreen(email: 'alex@example.com'),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final backButton = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backButton);
        await tester.pumpAndSettle();

        expect(find.byType(WelcomeScreen), findsOneWidget);
        expect(find.text(AppStrings.welcomeHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Renders EmailVerificationScreen without overflow across multiple device screen sizes',
      (WidgetTester tester) async {
        final screenSizes = [
          const Size(320, 568), // Small mobile (iPhone SE)
          const Size(390, 844), // Standard mobile (iPhone 13/14)
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const EmailVerificationScreen(email: 'alex@example.com'),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(
            find.text(AppStrings.emailVerificationHeading),
            findsOneWidget,
          );
          expect(find.text('alex@example.com'), findsOneWidget);
          expect(
            find.byKey(const Key('checkVerificationStatusButton')),
            findsOneWidget,
          );
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons and links support keyboard navigation and focus on Screen 013',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const EmailVerificationScreen(email: 'alex@example.com'),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(EmailVerificationScreen), findsOneWidget);
      },
    );
  });

  group('Screen 014 — Two-Factor Authentication (2FA) Screen Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
    });

    tearDown(() {
      AuthService.instance.resetToDefault();
    });

    testWidgets(
      'Unauthenticated state: displays authentication required banner and directs to sign in',
      (WidgetTester tester) async {
        // User is not authenticated
        expect(AuthService.instance.hasAuthenticatedSession, isFalse);

        await tester.pumpWidget(
          MaterialApp(
            home: const TwoFactorAuthScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.twoFactorHeading), findsOneWidget);
        expect(find.text(AppStrings.twoFactorSubtitle), findsOneWidget);
        expect(
          find.text(AppStrings.twoFactorStatusUnauthenticated),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.twoFactorStatusUnauthenticatedDesc),
          findsOneWidget,
        );

        final signInBtn = find.byKey(const Key('signInToManageMfaButton'));
        expect(signInBtn, findsOneWidget);
        await tester.ensureVisible(signInBtn);
        await tester.tap(signInBtn);
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Setup Required state: displays honest backend configuration steps when MFA is not configured on backend',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'alex@example.com',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const TwoFactorAuthScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Displays warning badge
        expect(
          find.text(AppStrings.twoFactorStatusSetupRequired),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.twoFactorBackendConfigTitle),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.twoFactorBackendPendingDesc),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.twoFactorBackendConfigStep1),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.twoFactorBackendConfigStep2),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.twoFactorBackendConfigStep3),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('checkMfaStatusButton')),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Check MFA Availability button queries status without fabricating enabled state',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'alex@example.com',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const TwoFactorAuthScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final checkBtn = find.byKey(const Key('checkMfaStatusButton'));
        await tester.ensureVisible(checkBtn);
        await tester.tap(checkBtn);
        await tester.pumpAndSettle();

        // Safeguard: State remains honestly not configured
        expect(AuthService.instance.isMfaEnabled, isFalse);
        expect(
          find.text(AppStrings.twoFactorStatusSetupRequired),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Not Enabled state: displays "Set Up 2FA" button when backend supports MFA but user is not enrolled',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'alex@example.com',
        );

        AuthService.instance.setMfaDelegates(
          getMfaStatus: () async => MfaStatus.disabled,
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const TwoFactorAuthScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.twoFactorStatusNotEnabled), findsOneWidget);
        expect(find.byKey(const Key('setupMfaButton')), findsOneWidget);
        expect(find.text(AppStrings.twoFactorSetupButton), findsOneWidget);
      },
    );

    testWidgets(
      'Enrollment flow: displays secret and code input when backend returns enrollment factor details',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'alex@example.com',
        );

        AuthService.instance.setMfaDelegates(
          getMfaStatus: () async => MfaStatus.disabled,
          enrollMfa: ({required String factorType}) async {
            return MfaEnrollResult.success(
              const MfaFactorDetails(
                id: 'factor_totp_999',
                secret: 'JBSWY3DPEHPK3PXP',
                uri: 'otpauth://totp/AITrust:alex@example.com?secret=JBSWY3DPEHPK3PXP',
              ),
            );
          },
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const TwoFactorAuthScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final setupBtn = find.byKey(const Key('setupMfaButton'));
        await tester.ensureVisible(setupBtn);
        await tester.tap(setupBtn);
        await tester.pumpAndSettle();

        // Secret and verification code field are rendered
        expect(find.text('JBSWY3DPEHPK3PXP'), findsOneWidget);
        expect(find.byKey(const Key('mfaCodeInputField')), findsOneWidget);
        expect(find.byKey(const Key('verifyMfaCodeButton')), findsOneWidget);
      },
    );

    testWidgets(
      'Validates 6-digit code during enrollment verification',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'alex@example.com',
        );

        AuthService.instance.setMfaDelegates(
          getMfaStatus: () async => MfaStatus.disabled,
          enrollMfa: ({required String factorType}) async {
            return MfaEnrollResult.success(
              const MfaFactorDetails(
                id: 'factor_totp_999',
                secret: 'JBSWY3DPEHPK3PXP',
              ),
            );
          },
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const TwoFactorAuthScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.ensureVisible(find.byKey(const Key('setupMfaButton')));
        await tester.tap(find.byKey(const Key('setupMfaButton')));
        await tester.pumpAndSettle();

        // Tap verify without entering code
        final verifyBtn = find.byKey(const Key('verifyMfaCodeButton'));
        await tester.ensureVisible(verifyBtn);
        await tester.tap(verifyBtn);
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.twoFactorCodeRequiredError),
          findsOneWidget,
        );

        // Enter invalid short code
        await tester.enterText(find.byKey(const Key('mfaCodeInputField')), '123');
        await tester.tap(verifyBtn);
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.twoFactorCodeInvalidError),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Failed code verification displays error banner without activating 2FA',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'alex@example.com',
        );

        AuthService.instance.setMfaDelegates(
          getMfaStatus: () async => MfaStatus.disabled,
          enrollMfa: ({required String factorType}) async {
            return MfaEnrollResult.success(
              const MfaFactorDetails(
                id: 'factor_totp_999',
                secret: 'JBSWY3DPEHPK3PXP',
              ),
            );
          },
          verifyMfa: ({required String factorId, required String code}) async {
            return MfaVerifyResult.failure(
              AppStrings.twoFactorCodeInvalidError,
              AuthErrorCode.invalidCredentials,
            );
          },
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const TwoFactorAuthScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.ensureVisible(find.byKey(const Key('setupMfaButton')));
        await tester.tap(find.byKey(const Key('setupMfaButton')));
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('mfaCodeInputField')),
          '000000',
        );

        final verifyBtn = find.byKey(const Key('verifyMfaCodeButton'));
        await tester.ensureVisible(verifyBtn);
        await tester.tap(verifyBtn);
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('mfaErrorBanner')), findsOneWidget);
        expect(
          find.text(AppStrings.twoFactorCodeInvalidError),
          findsOneWidget,
        );
        expect(AuthService.instance.isMfaEnabled, isFalse);
      },
    );

    testWidgets(
      'Successful code verification activates 2FA, displays toast, and renders active enrolled state',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'alex@example.com',
        );

        AuthService.instance.setMfaDelegates(
          getMfaStatus: () async => MfaStatus.disabled,
          enrollMfa: ({required String factorType}) async {
            return MfaEnrollResult.success(
              const MfaFactorDetails(
                id: 'factor_totp_999',
                secret: 'JBSWY3DPEHPK3PXP',
              ),
            );
          },
          verifyMfa: ({required String factorId, required String code}) async {
            return MfaVerifyResult.success();
          },
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const TwoFactorAuthScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.ensureVisible(find.byKey(const Key('setupMfaButton')));
        await tester.tap(find.byKey(const Key('setupMfaButton')));
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('mfaCodeInputField')),
          '123456',
        );

        final verifyBtn = find.byKey(const Key('verifyMfaCodeButton'));
        await tester.ensureVisible(verifyBtn);
        await tester.tap(verifyBtn);
        await tester.pumpAndSettle();

        // 2FA is now enabled
        expect(AuthService.instance.isMfaEnabled, isTrue);
        expect(find.text(AppStrings.twoFactorStatusEnabled), findsOneWidget);
        expect(find.text(AppStrings.twoFactorEnrolledBadge), findsOneWidget);
        expect(find.byKey(const Key('disableMfaButton')), findsOneWidget);
      },
    );

    testWidgets(
      'Enrolled state: tapping "Disable 2FA" and canceling dialog keeps 2FA enabled',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'alex@example.com',
          mfaStatus: MfaStatus.enrolled,
        );

        AuthService.instance.setMfaDelegates(
          getMfaStatus: () async => MfaStatus.enrolled,
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const TwoFactorAuthScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.twoFactorStatusEnabled), findsOneWidget);

        final disableBtn = find.byKey(const Key('disableMfaButton'));
        await tester.ensureVisible(disableBtn);
        await tester.tap(disableBtn);
        await tester.pumpAndSettle();

        // Dialog is visible
        expect(
          find.text(AppStrings.twoFactorDisableConfirmTitle),
          findsOneWidget,
        );

        // Tap cancel
        await tester.tap(find.text(AppStrings.twoFactorCancelAction));
        await tester.pumpAndSettle();

        // 2FA remains active
        expect(find.text(AppStrings.twoFactorStatusEnabled), findsOneWidget);
      },
    );

    testWidgets(
      'Enrolled state: confirming disable dialog calls unenroll and disables 2FA',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'alex@example.com',
          mfaStatus: MfaStatus.enrolled,
        );

        bool unenrollCalled = false;
        AuthService.instance.setMfaDelegates(
          getMfaStatus: () async => MfaStatus.enrolled,
          unenrollMfa: ({required String factorId}) async {
            unenrollCalled = true;
            return MfaUnenrollResult.success();
          },
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const TwoFactorAuthScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final disableBtn = find.byKey(const Key('disableMfaButton'));
        await tester.ensureVisible(disableBtn);
        await tester.tap(disableBtn);
        await tester.pumpAndSettle();

        // Confirm disable
        final confirmBtn = find.byKey(const Key('confirmDisableMfaButton'));
        await tester.tap(confirmBtn);
        await tester.pumpAndSettle();

        expect(unenrollCalled, isTrue);
        expect(AuthService.instance.isMfaEnabled, isFalse);
        expect(
          find.text(AppStrings.twoFactorDisabledSuccessToast),
          findsAtLeastNWidgets(1),
        );
      },
    );

    testWidgets(
      'Renders TwoFactorAuthScreen without overflow across multiple device screen sizes',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'alex@example.com',
        );

        final screenSizes = [
          const Size(320, 568), // Small mobile
          const Size(390, 844), // Standard mobile
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const TwoFactorAuthScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.text(AppStrings.twoFactorHeading), findsOneWidget);
          expect(find.byKey(const Key('mfaStatusText')), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons and links support keyboard navigation and focus on Screen 014',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'alex@example.com',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const TwoFactorAuthScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(TwoFactorAuthScreen), findsOneWidget);
      },
    );
  });

  group('Screen 015 — Forgot Password Screen Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
    });

    tearDown(() {
      AuthService.instance.resetToDefault();
    });

    testWidgets(
      'Renders all forgot password elements: logo, heading, subtitle, email field, submit button, and back link',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const ForgotPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.forgotPasswordHeading), findsOneWidget);
        expect(find.text(AppStrings.forgotPasswordSubtitle), findsOneWidget);
        expect(
          find.byKey(const Key('forgotPasswordEmailField')),
          findsOneWidget,
        );
        expect(find.byKey(const Key('sendResetLinkButton')), findsOneWidget);
        expect(find.text(AppStrings.forgotPasswordSubmitButton), findsOneWidget);
        expect(find.byKey(const Key('backToLoginLink')), findsOneWidget);
        expect(find.text(AppStrings.forgotPasswordBackToLogin), findsOneWidget);
        expect(find.byType(IdentityTrustLogo), findsOneWidget);
        expect(find.byTooltip(AppStrings.backTooltip), findsOneWidget);
      },
    );

    testWidgets(
      'Prepopulates email when provided via initialEmail argument',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const ForgotPasswordScreen(initialEmail: 'alex@example.com'),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text('alex@example.com'), findsOneWidget);
      },
    );

    testWidgets(
      'Validation: shows field-specific error when email is empty',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const ForgotPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final submitBtn = find.byKey(const Key('sendResetLinkButton'));
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.emailRequiredError), findsOneWidget);
      },
    );

    testWidgets(
      'Validation: shows field-specific error when email format is invalid',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const ForgotPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('forgotPasswordEmailField')),
          'invalid-email-address',
        );

        final submitBtn = find.byKey(const Key('sendResetLinkButton'));
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.emailInvalidError), findsOneWidget);
      },
    );

    testWidgets(
      'Displays loading indicator while reset request is in flight',
      (WidgetTester tester) async {
        final completer = Completer<AuthPasswordResetResult>();
        AuthService.instance.setResetPasswordDelegate(({
          required String email,
          String? redirectTo,
        }) {
          return completer.future;
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ForgotPasswordScreen(initialEmail: 'alex@example.com'),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final submitBtn = find.byKey(const Key('sendResetLinkButton'));
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pump(); // start frame

        expect(find.byType(CircularProgressIndicator), findsOneWidget);

        completer.complete(
          AuthPasswordResetResult.success(email: 'alex@example.com'),
        );
        await tester.pumpAndSettle();

        expect(find.byType(CircularProgressIndicator), findsNothing);
      },
    );

    testWidgets(
      'Successful submission renders accessible confirmation card with privacy-safe message without leaking user existence',
      (WidgetTester tester) async {
        AuthService.instance.setResetPasswordDelegate(({
          required String email,
          String? redirectTo,
        }) async {
          return AuthPasswordResetResult.success(email: email);
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ForgotPasswordScreen(initialEmail: 'alex@example.com'),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final submitBtn = find.byKey(const Key('sendResetLinkButton'));
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        // Confirmation card is visible
        expect(find.byKey(const Key('resetSuccessCard')), findsOneWidget);
        expect(
          find.text(AppStrings.forgotPasswordSuccessTitle),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.forgotPasswordSuccessMessage),
          findsOneWidget,
        );
        expect(find.text('alex@example.com'), findsOneWidget);
        expect(
          find.text(AppStrings.forgotPasswordDeliveryDisclaimer),
          findsOneWidget,
        );
        expect(find.byKey(const Key('sendAnotherResetButton')), findsOneWidget);

        // Security safeguard: Does NOT change session or reveal private data
        expect(AuthService.instance.hasAuthenticatedSession, isFalse);
      },
    );

    testWidgets(
      'Tapping "Send Another Link" restores the input form and clears previous state',
      (WidgetTester tester) async {
        AuthService.instance.setResetPasswordDelegate(({
          required String email,
          String? redirectTo,
        }) async {
          return AuthPasswordResetResult.success(email: email);
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ForgotPasswordScreen(initialEmail: 'alex@example.com'),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.tap(find.byKey(const Key('sendResetLinkButton')));
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('resetSuccessCard')), findsOneWidget);

        // Tap send another link
        final sendAnotherBtn = find.byKey(const Key('sendAnotherResetButton'));
        await tester.ensureVisible(sendAnotherBtn);
        await tester.tap(sendAnotherBtn);
        await tester.pumpAndSettle();

        // Form is restored
        expect(find.byKey(const Key('resetSuccessCard')), findsNothing);
        expect(
          find.byKey(const Key('forgotPasswordEmailField')),
          findsOneWidget,
        );
        expect(find.byKey(const Key('sendResetLinkButton')), findsOneWidget);
      },
    );

    testWidgets(
      'Handles network error and rate limit gracefully with accessible error banner',
      (WidgetTester tester) async {
        AuthService.instance.setResetPasswordDelegate(({
          required String email,
          String? redirectTo,
        }) async {
          return AuthPasswordResetResult.failure(
            errorMessage: AppStrings.authErrorNetwork,
            errorCode: AuthErrorCode.networkError,
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ForgotPasswordScreen(initialEmail: 'alex@example.com'),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.tap(find.byKey(const Key('sendResetLinkButton')));
        await tester.pumpAndSettle();

        expect(
          find.byKey(const Key('forgotPasswordErrorBanner')),
          findsOneWidget,
        );
        expect(find.text(AppStrings.authErrorNetwork), findsOneWidget);
        expect(find.byKey(const Key('resetSuccessCard')), findsNothing);
      },
    );

    testWidgets(
      'Tapping "Back to Login" navigates back to LoginScreen route',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const ForgotPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final backLink = find.byKey(const Key('backToLoginLink'));
        await tester.ensureVisible(backLink);
        await tester.tap(backLink);
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
        expect(find.text(AppStrings.loginHeading), findsOneWidget);
      },
    );

    testWidgets(
      'Top back button returns to Login screen when opened standalone',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const ForgotPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final backBtn = find.byTooltip(AppStrings.backTooltip);
        await tester.tap(backBtn);
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Navigating from LoginScreen via "Forgot Password?" opens ForgotPasswordScreen and prepopulates email',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const LoginScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Enter email in login screen
        await tester.enterText(
          find.byKey(const Key('loginEmailField')),
          'user@example.com',
        );

        final forgotLink = find.byKey(const Key('forgotPasswordLink'));
        await tester.ensureVisible(forgotLink);
        await tester.tap(forgotLink);
        await tester.pumpAndSettle();

        expect(find.byType(ForgotPasswordScreen), findsOneWidget);
        expect(find.text(AppStrings.forgotPasswordHeading), findsOneWidget);
        expect(find.text('user@example.com'), findsOneWidget);
      },
    );

    testWidgets(
      'Renders ForgotPasswordScreen without overflow across multiple device screen sizes',
      (WidgetTester tester) async {
        final screenSizes = [
          const Size(320, 568), // Small mobile
          const Size(390, 844), // Standard mobile
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const ForgotPasswordScreen(
                initialEmail: 'alex@example.com',
              ),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.text(AppStrings.forgotPasswordHeading), findsOneWidget);
          expect(find.byKey(const Key('sendResetLinkButton')), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons and links support keyboard navigation and focus on Screen 015',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const ForgotPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(ForgotPasswordScreen), findsOneWidget);
      },
    );
  });

  group('Screen 016 — Reset Password Screen Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
    });

    tearDown(() {
      AuthService.instance.resetToDefault();
    });

    testWidgets(
      'Missing recovery session: displays invalid/expired recovery link card and blocks form',
      (WidgetTester tester) async {
        // Recovery session is not active
        expect(AuthService.instance.hasRecoverySession, isFalse);

        await tester.pumpWidget(
          MaterialApp(
            home: const ResetPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.resetPasswordHeading), findsOneWidget);
        expect(find.text(AppStrings.resetPasswordSubtitle), findsOneWidget);
        expect(
          find.byKey(const Key('missingRecoverySessionCard')),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.resetPasswordInvalidLinkTitle),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.resetPasswordInvalidLinkMessage),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('requestNewLinkButton')),
          findsOneWidget,
        );

        // Security safeguard: Password inputs are NOT rendered without session
        expect(find.byKey(const Key('newPasswordField')), findsNothing);
        expect(find.byKey(const Key('updatePasswordButton')), findsNothing);

        // Tapping request new link navigates to ForgotPasswordScreen
        final reqBtn = find.byKey(const Key('requestNewLinkButton'));
        await tester.ensureVisible(reqBtn);
        await tester.tap(reqBtn);
        await tester.pumpAndSettle();

        expect(find.byType(ForgotPasswordScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Valid recovery session: renders password fields, checklist, and submit button',
      (WidgetTester tester) async {
        AuthService.instance.setRecoverySessionForTesting(true);

        await tester.pumpWidget(
          MaterialApp(
            home: const ResetPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.resetPasswordHeading), findsOneWidget);
        expect(find.byKey(const Key('newPasswordField')), findsOneWidget);
        expect(
          find.byKey(const Key('confirmNewPasswordField')),
          findsOneWidget,
        );
        expect(find.byKey(const Key('updatePasswordButton')), findsOneWidget);
        expect(find.text(AppStrings.resetPasswordSubmitButton), findsOneWidget);
        expect(find.text(AppStrings.passwordPolicyHeader), findsOneWidget);
        expect(find.text(AppStrings.passwordPolicyLength), findsOneWidget);
        expect(find.text(AppStrings.passwordPolicyUppercase), findsOneWidget);
        expect(find.text(AppStrings.passwordPolicyLowercase), findsOneWidget);
        expect(find.text(AppStrings.passwordPolicyNumber), findsOneWidget);
        expect(find.byType(IdentityTrustLogo), findsOneWidget);
      },
    );

    testWidgets(
      'Toggles new password and confirm password visibility correctly',
      (WidgetTester tester) async {
        AuthService.instance.setRecoverySessionForTesting(true);

        await tester.pumpWidget(
          MaterialApp(
            home: const ResetPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final newPasswordField = tester.widget<EditableText>(
          find.descendant(
            of: find.byKey(const Key('newPasswordField')),
            matching: find.byType(EditableText),
          ),
        );
        expect(newPasswordField.obscureText, isTrue);

        // Tap toggle new password button
        await tester.tap(
          find.byKey(const Key('toggleNewPasswordVisibilityButton')),
        );
        await tester.pumpAndSettle();

        final newPasswordFieldToggled = tester.widget<EditableText>(
          find.descendant(
            of: find.byKey(const Key('newPasswordField')),
            matching: find.byType(EditableText),
          ),
        );
        expect(newPasswordFieldToggled.obscureText, isFalse);

        // Tap toggle confirm password button
        final confirmField = tester.widget<EditableText>(
          find.descendant(
            of: find.byKey(const Key('confirmNewPasswordField')),
            matching: find.byType(EditableText),
          ),
        );
        expect(confirmField.obscureText, isTrue);

        final toggleConfirmBtn = find.byKey(
          const Key('toggleConfirmPasswordVisibilityButton'),
        );
        await tester.ensureVisible(toggleConfirmBtn);
        await tester.tap(toggleConfirmBtn);
        await tester.pumpAndSettle();

        final confirmFieldToggled = tester.widget<EditableText>(
          find.descendant(
            of: find.byKey(const Key('confirmNewPasswordField')),
            matching: find.byType(EditableText),
          ),
        );
        expect(confirmFieldToggled.obscureText, isFalse);
      },
    );

    testWidgets(
      'Updates password requirements checklist dynamically as text changes',
      (WidgetTester tester) async {
        AuthService.instance.setRecoverySessionForTesting(true);

        await tester.pumpWidget(
          MaterialApp(
            home: const ResetPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final newPassField = find.byKey(const Key('newPasswordField'));

        // Enter lowercase only
        await tester.enterText(newPassField, 'abcdefgh');
        await tester.pumpAndSettle();

        // Uppercase and number should still be unsatisfied
        expect(
          find.byWidgetPredicate(
            (widget) =>
                widget is PasswordRequirementItem &&
                widget.label == AppStrings.passwordPolicyUppercase &&
                !widget.isMet,
          ),
          findsOneWidget,
        );

        // Enter uppercase and digit to satisfy all criteria
        await tester.enterText(newPassField, 'Password123');
        await tester.pumpAndSettle();

        expect(
          find.byWidgetPredicate(
            (widget) =>
                widget is PasswordRequirementItem &&
                widget.label == AppStrings.passwordPolicyLength &&
                widget.isMet,
          ),
          findsOneWidget,
        );
        expect(
          find.byWidgetPredicate(
            (widget) =>
                widget is PasswordRequirementItem &&
                widget.label == AppStrings.passwordPolicyUppercase &&
                widget.isMet,
          ),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Validation: shows field-specific error when password is empty or violates policy',
      (WidgetTester tester) async {
        AuthService.instance.setRecoverySessionForTesting(true);

        await tester.pumpWidget(
          MaterialApp(
            home: const ResetPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final submitBtn = find.byKey(const Key('updatePasswordButton'));
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.resetPasswordRequiredError),
          findsOneWidget,
        );

        // Enter weak password
        await tester.enterText(
          find.byKey(const Key('newPasswordField')),
          'short',
        );
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.passwordPolicyNotMetError),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Validation: shows field-specific error when confirm password is empty or mismatches',
      (WidgetTester tester) async {
        AuthService.instance.setRecoverySessionForTesting(true);

        await tester.pumpWidget(
          MaterialApp(
            home: const ResetPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('newPasswordField')),
          'Password123',
        );

        final submitBtn = find.byKey(const Key('updatePasswordButton'));
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.confirmPasswordRequiredError),
          findsOneWidget,
        );

        // Enter non-matching confirmation
        await tester.enterText(
          find.byKey(const Key('confirmNewPasswordField')),
          'DifferentPassword456',
        );
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.passwordsDoNotMatchError),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Displays loading spinner while update is processing',
      (WidgetTester tester) async {
        AuthService.instance.setRecoverySessionForTesting(true);

        final completer = Completer<AuthPasswordUpdateResult>();
        AuthService.instance.setUpdatePasswordDelegate(({
          required String newPassword,
        }) {
          return completer.future;
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ResetPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('newPasswordField')),
          'Password123',
        );
        await tester.enterText(
          find.byKey(const Key('confirmNewPasswordField')),
          'Password123',
        );

        final submitBtn = find.byKey(const Key('updatePasswordButton'));
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pump(); // Start frame

        expect(find.byType(CircularProgressIndicator), findsOneWidget);

        completer.complete(AuthPasswordUpdateResult.success());
        await tester.pumpAndSettle();

        expect(find.byType(CircularProgressIndicator), findsNothing);
      },
    );

    testWidgets(
      'Handles update failure and displays accessible error banner',
      (WidgetTester tester) async {
        AuthService.instance.setRecoverySessionForTesting(true);

        AuthService.instance.setUpdatePasswordDelegate(({
          required String newPassword,
        }) async {
          return AuthPasswordUpdateResult.failure(
            AppStrings.authErrorNetwork,
            AuthErrorCode.networkError,
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ResetPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('newPasswordField')),
          'Password123',
        );
        await tester.enterText(
          find.byKey(const Key('confirmNewPasswordField')),
          'Password123',
        );

        final submitBtn = find.byKey(const Key('updatePasswordButton'));
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(
          find.byKey(const Key('resetPasswordErrorBanner')),
          findsOneWidget,
        );
        expect(find.text(AppStrings.authErrorNetwork), findsOneWidget);
        expect(find.byKey(const Key('resetSuccessCard')), findsNothing);
      },
    );

    testWidgets(
      'Successful password update renders confirmation card and resets recovery session',
      (WidgetTester tester) async {
        AuthService.instance.setRecoverySessionForTesting(true);

        bool updateInvoked = false;
        AuthService.instance.setUpdatePasswordDelegate(({
          required String newPassword,
        }) async {
          updateInvoked = true;
          return AuthPasswordUpdateResult.success();
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ResetPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('newPasswordField')),
          'Password123',
        );
        await tester.enterText(
          find.byKey(const Key('confirmNewPasswordField')),
          'Password123',
        );

        final submitBtn = find.byKey(const Key('updatePasswordButton'));
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(updateInvoked, isTrue);

        // Security safeguard: Recovery session is consumed/reset
        expect(AuthService.instance.hasRecoverySession, isFalse);

        // Success card is rendered
        expect(find.byKey(const Key('resetSuccessCard')), findsOneWidget);
        expect(
          find.text(AppStrings.resetPasswordSuccessTitle),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.resetPasswordSuccessMessage),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('continueToSignInButton')),
          findsOneWidget,
        );

        // Tapping continue navigates to LoginScreen
        final continueBtn = find.byKey(const Key('continueToSignInButton'));
        await tester.ensureVisible(continueBtn);
        await tester.tap(continueBtn);
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'AuthService rejects updatePassword attempt without recovery session',
      (WidgetTester tester) async {
        AuthService.instance.setRecoverySessionForTesting(false);

        final result = await AuthService.instance.updatePassword(
          newPassword: 'Password123',
        );

        expect(result.isSuccess, isFalse);
        expect(result.errorCode, AuthErrorCode.sessionExpired);
      },
    );

    testWidgets(
      'Top back button and secondary link navigate back to Sign In',
      (WidgetTester tester) async {
        AuthService.instance.setRecoverySessionForTesting(true);

        await tester.pumpWidget(
          MaterialApp(
            home: const ResetPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final backLink = find.byKey(const Key('backToSignInLink'));
        await tester.ensureVisible(backLink);
        await tester.tap(backLink);
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Renders ResetPasswordScreen without overflow across multiple device screen sizes',
      (WidgetTester tester) async {
        AuthService.instance.setRecoverySessionForTesting(true);

        final screenSizes = [
          const Size(320, 568), // Small mobile
          const Size(390, 844), // Standard mobile
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const ResetPasswordScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.text(AppStrings.resetPasswordHeading), findsOneWidget);
          expect(
            find.byKey(const Key('updatePasswordButton')),
            findsOneWidget,
          );
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons and inputs support keyboard navigation and focus on Screen 016',
      (WidgetTester tester) async {
        AuthService.instance.setRecoverySessionForTesting(true);

        await tester.pumpWidget(
          MaterialApp(
            home: const ResetPasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(ResetPasswordScreen), findsOneWidget);
      },
    );
  });

  group('Screen 017 — Change Password Screen Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
    });

    tearDown(() {
      AuthService.instance.resetToDefault();
    });

    testWidgets(
      'Unauthenticated user: renders authentication required card and blocks form',
      (WidgetTester tester) async {
        AuthService.instance.resetToDefault();

        await tester.pumpWidget(
          MaterialApp(
            home: const ChangePasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('unauthenticatedCard')), findsOneWidget);
        expect(
          find.text(AppStrings.changePasswordUnauthenticatedTitle),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.changePasswordUnauthenticatedDesc),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('signInToChangePasswordButton')),
          findsOneWidget,
        );

        // Security safeguard: Password inputs are NOT rendered without session
        expect(find.byKey(const Key('currentPasswordField')), findsNothing);
        expect(find.byKey(const Key('newPasswordField')), findsNothing);
        expect(find.byKey(const Key('confirmNewPasswordField')), findsNothing);
        expect(find.byKey(const Key('updatePasswordButton')), findsNothing);

        // Tapping sign in navigates to LoginScreen
        final signInBtn = find.byKey(const Key('signInToChangePasswordButton'));
        await tester.ensureVisible(signInBtn);
        await tester.tap(signInBtn);
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Authenticated user: renders form fields, password checklist, and update button',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'verified_user@example.com',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ChangePasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.changePasswordHeading), findsOneWidget);
        expect(find.text(AppStrings.changePasswordSubtitle), findsOneWidget);
        expect(find.byKey(const Key('currentPasswordField')), findsOneWidget);
        expect(find.byKey(const Key('newPasswordField')), findsOneWidget);
        expect(
          find.byKey(const Key('confirmNewPasswordField')),
          findsOneWidget,
        );
        expect(find.byKey(const Key('updatePasswordButton')), findsOneWidget);
        expect(find.text(AppStrings.changePasswordSubmitButton), findsOneWidget);
        expect(find.text(AppStrings.passwordPolicyHeader), findsOneWidget);
        expect(find.text(AppStrings.passwordPolicyLength), findsOneWidget);
        expect(find.text(AppStrings.passwordPolicyUppercase), findsOneWidget);
        expect(find.text(AppStrings.passwordPolicyLowercase), findsOneWidget);
        expect(find.text(AppStrings.passwordPolicyNumber), findsOneWidget);
        expect(find.byType(IdentityTrustLogo), findsOneWidget);
      },
    );

    testWidgets(
      'Toggles visibility for current, new, and confirm password fields',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'verified_user@example.com',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ChangePasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // 1. Current password toggle
        final currentField = tester.widget<EditableText>(
          find.descendant(
            of: find.byKey(const Key('currentPasswordField')),
            matching: find.byType(EditableText),
          ),
        );
        expect(currentField.obscureText, isTrue);

        final toggleCurrentBtn = find.byKey(
          const Key('toggleCurrentPasswordVisibilityButton'),
        );
        await tester.ensureVisible(toggleCurrentBtn);
        await tester.tap(toggleCurrentBtn);
        await tester.pumpAndSettle();

        final currentFieldToggled = tester.widget<EditableText>(
          find.descendant(
            of: find.byKey(const Key('currentPasswordField')),
            matching: find.byType(EditableText),
          ),
        );
        expect(currentFieldToggled.obscureText, isFalse);

        // 2. New password toggle
        final newField = tester.widget<EditableText>(
          find.descendant(
            of: find.byKey(const Key('newPasswordField')),
            matching: find.byType(EditableText),
          ),
        );
        expect(newField.obscureText, isTrue);

        final toggleNewBtn = find.byKey(
          const Key('toggleNewPasswordVisibilityButton'),
        );
        await tester.ensureVisible(toggleNewBtn);
        await tester.tap(toggleNewBtn);
        await tester.pumpAndSettle();

        final newFieldToggled = tester.widget<EditableText>(
          find.descendant(
            of: find.byKey(const Key('newPasswordField')),
            matching: find.byType(EditableText),
          ),
        );
        expect(newFieldToggled.obscureText, isFalse);

        // 3. Confirm password toggle
        final confirmField = tester.widget<EditableText>(
          find.descendant(
            of: find.byKey(const Key('confirmNewPasswordField')),
            matching: find.byType(EditableText),
          ),
        );
        expect(confirmField.obscureText, isTrue);

        final toggleConfirmBtn = find.byKey(
          const Key('toggleConfirmPasswordVisibilityButton'),
        );
        await tester.ensureVisible(toggleConfirmBtn);
        await tester.tap(toggleConfirmBtn);
        await tester.pumpAndSettle();

        final confirmFieldToggled = tester.widget<EditableText>(
          find.descendant(
            of: find.byKey(const Key('confirmNewPasswordField')),
            matching: find.byType(EditableText),
          ),
        );
        expect(confirmFieldToggled.obscureText, isFalse);
      },
    );

    testWidgets(
      'Updates password requirements checklist dynamically as text is entered',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'verified_user@example.com',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ChangePasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final newPassField = find.byKey(const Key('newPasswordField'));
        await tester.ensureVisible(newPassField);

        // Enter lowercase letters only
        await tester.enterText(newPassField, 'abcdefgh');
        await tester.pumpAndSettle();

        // Length & lowercase met, uppercase & number unmet
        expect(
          find.byWidgetPredicate(
            (widget) =>
                widget is PasswordRequirementItem &&
                widget.label == AppStrings.passwordPolicyUppercase &&
                !widget.isMet,
          ),
          findsOneWidget,
        );

        // Enter full compliant password
        await tester.enterText(newPassField, 'SecurePassword123');
        await tester.pumpAndSettle();

        expect(
          find.byWidgetPredicate(
            (widget) =>
                widget is PasswordRequirementItem &&
                widget.label == AppStrings.passwordPolicyLength &&
                widget.isMet,
          ),
          findsOneWidget,
        );
        expect(
          find.byWidgetPredicate(
            (widget) =>
                widget is PasswordRequirementItem &&
                widget.label == AppStrings.passwordPolicyUppercase &&
                widget.isMet,
          ),
          findsOneWidget,
        );
        expect(
          find.byWidgetPredicate(
            (widget) =>
                widget is PasswordRequirementItem &&
                widget.label == AppStrings.passwordPolicyNumber &&
                widget.isMet,
          ),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Validation: shows error when current password is empty',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'verified_user@example.com',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ChangePasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final submitBtn = find.byKey(const Key('updatePasswordButton'));
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.currentPasswordRequiredError),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Validation: shows error when new password is weak or same as current',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'verified_user@example.com',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ChangePasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final currentField = find.byKey(const Key('currentPasswordField'));
        final newField = find.byKey(const Key('newPasswordField'));
        final submitBtn = find.byKey(const Key('updatePasswordButton'));

        await tester.enterText(currentField, 'OldPassword123');
        await tester.enterText(newField, 'weak');
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.passwordPolicyNotMetError),
          findsOneWidget,
        );

        // Same password as current
        await tester.enterText(newField, 'OldPassword123');
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.changePasswordSamePasswordError),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Validation: shows error when confirm password is empty or does not match',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'verified_user@example.com',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ChangePasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final currentField = find.byKey(const Key('currentPasswordField'));
        final newField = find.byKey(const Key('newPasswordField'));
        final confirmField = find.byKey(const Key('confirmNewPasswordField'));
        final submitBtn = find.byKey(const Key('updatePasswordButton'));

        await tester.enterText(currentField, 'CurrentPass123');
        await tester.enterText(newField, 'NewSecurePass123');
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.confirmPasswordRequiredError),
          findsOneWidget,
        );

        // Mismatched confirmation
        await tester.enterText(confirmField, 'DifferentPass456');
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.passwordsDoNotMatchError),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Displays loading indicator during in-flight update and prevents duplicate submission',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'verified_user@example.com',
        );

        final completer = Completer<AuthPasswordUpdateResult>();
        AuthService.instance.setChangePasswordDelegate(({
          required String currentPassword,
          required String newPassword,
        }) {
          return completer.future;
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ChangePasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('currentPasswordField')),
          'CurrentPass123',
        );
        await tester.enterText(
          find.byKey(const Key('newPasswordField')),
          'NewSecurePass123',
        );
        await tester.enterText(
          find.byKey(const Key('confirmNewPasswordField')),
          'NewSecurePass123',
        );

        final submitBtn = find.byKey(const Key('updatePasswordButton'));
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pump(); // Start frame

        expect(find.byType(CircularProgressIndicator), findsOneWidget);

        completer.complete(AuthPasswordUpdateResult.success());
        await tester.pumpAndSettle();

        expect(find.byType(CircularProgressIndicator), findsNothing);
      },
    );

    testWidgets(
      'Handles incorrect current password and renders accessible error banner',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'verified_user@example.com',
        );

        AuthService.instance.setChangePasswordDelegate(({
          required String currentPassword,
          required String newPassword,
        }) async {
          return AuthPasswordUpdateResult.failure(
            AppStrings.changePasswordIncorrectCurrent,
            AuthErrorCode.invalidCredentials,
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ChangePasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('currentPasswordField')),
          'WrongPassword123',
        );
        await tester.enterText(
          find.byKey(const Key('newPasswordField')),
          'NewSecurePass123',
        );
        await tester.enterText(
          find.byKey(const Key('confirmNewPasswordField')),
          'NewSecurePass123',
        );

        final submitBtn = find.byKey(const Key('updatePasswordButton'));
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(
          find.byKey(const Key('changePasswordErrorBanner')),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.changePasswordIncorrectCurrent),
          findsOneWidget,
        );
        expect(find.byKey(const Key('changePasswordSuccessCard')), findsNothing);
      },
    );

    testWidgets(
      'Successful password update renders confirmation card, preserves session, and navigates to workspace',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'verified_user@example.com',
        );

        bool changeInvoked = false;
        AuthService.instance.setChangePasswordDelegate(({
          required String currentPassword,
          required String newPassword,
        }) async {
          changeInvoked = true;
          return AuthPasswordUpdateResult.success();
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ChangePasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.enterText(
          find.byKey(const Key('currentPasswordField')),
          'CurrentPass123',
        );
        await tester.enterText(
          find.byKey(const Key('newPasswordField')),
          'NewSecurePass123',
        );
        await tester.enterText(
          find.byKey(const Key('confirmNewPasswordField')),
          'NewSecurePass123',
        );

        final submitBtn = find.byKey(const Key('updatePasswordButton'));
        await tester.ensureVisible(submitBtn);
        await tester.tap(submitBtn);
        await tester.pumpAndSettle();

        expect(changeInvoked, isTrue);

        // Security safeguard: Active session remains authenticated
        expect(AuthService.instance.hasAuthenticatedSession, isTrue);

        // Confirmation card rendered
        expect(
          find.byKey(const Key('changePasswordSuccessCard')),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.changePasswordSuccessTitle),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.changePasswordSuccessMessage),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('backToWorkspaceButton')),
          findsOneWidget,
        );

        // Tapping back to workspace navigates to workspace placeholder
        final backBtn = find.byKey(const Key('backToWorkspaceButton'));
        await tester.ensureVisible(backBtn);
        await tester.tap(backBtn);
        await tester.pumpAndSettle();

        expect(find.byType(RoutePlaceholderScreen), findsOneWidget);
      },
    );

    testWidgets(
      'AuthService rejects changePassword attempt without active session or if passwords match',
      (WidgetTester tester) async {
        AuthService.instance.resetToDefault();

        // 1. Without session
        final unauthResult = await AuthService.instance.changePassword(
          currentPassword: 'OldPass123',
          newPassword: 'NewPass123',
        );
        expect(unauthResult.isSuccess, isFalse);
        expect(unauthResult.errorCode, AuthErrorCode.sessionExpired);

        // 2. With session but identical password
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'test@example.com',
        );
        final sameResult = await AuthService.instance.changePassword(
          currentPassword: 'SamePass123',
          newPassword: 'SamePass123',
        );
        expect(sameResult.isSuccess, isFalse);
        expect(sameResult.errorCode, AuthErrorCode.invalidCredentials);
      },
    );

    testWidgets(
      'Top back button and footer link navigate back to workspace',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'verified_user@example.com',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ChangePasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final backLink = find.byKey(const Key('backToWorkspaceLink'));
        await tester.ensureVisible(backLink);
        await tester.tap(backLink);
        await tester.pumpAndSettle();

        expect(find.byType(RoutePlaceholderScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Renders ChangePasswordScreen without overflow across multiple device screen sizes',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'verified_user@example.com',
        );

        final screenSizes = [
          const Size(320, 568), // Small mobile
          const Size(390, 844), // Standard mobile
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const ChangePasswordScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.text(AppStrings.changePasswordHeading), findsOneWidget);
          expect(
            find.byKey(const Key('updatePasswordButton')),
            findsOneWidget,
          );
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons and inputs support keyboard navigation and focus on Screen 017',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'verified_user@example.com',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ChangePasswordScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(ChangePasswordScreen), findsOneWidget);
      },
    );
  });

  group('Screen 018 — Account Lockout & Security Alerts Screen Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
    });

    tearDown(() {
      AuthService.instance.resetToDefault();
    });

    testWidgets(
      'Authenticated user: renders security posture summary with real data',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
          mfaStatus: MfaStatus.enrolled,
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.securityAlertsHeading), findsOneWidget);
        expect(find.text(AppStrings.securityAlertsSubtitle), findsOneWidget);
        expect(find.byKey(const Key('securitySummaryCard')), findsOneWidget);
        expect(find.text('officer@digitaltrust.ai'), findsOneWidget);
        expect(find.text(AppStrings.securityStatusMfaEnabled), findsOneWidget);
        expect(
          find.text(AppStrings.securityStatusEmailConfirmed),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.securityStatusStandingNormal),
          findsOneWidget,
        );
        expect(find.byType(IdentityTrustLogo), findsOneWidget);
      },
    );

    testWidgets(
      'Unauthenticated state: renders truthful status reflecting no active session',
      (WidgetTester tester) async {
        AuthService.instance.resetToDefault();

        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.securityStatusNoSession), findsOneWidget);
        expect(
          find.text(AppStrings.securityStatusEmailUnconfirmed),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Confirmed lockout via arguments: renders lockout banner with retry guidance and recovery links',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(
              initialIsLockedOut: true,
              retryAfterSeconds: 45,
              lockoutMessage: 'Too many failed password attempts.',
            ),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('lockoutAlertBanner')), findsOneWidget);
        expect(
          find.text(AppStrings.securityLockoutBannerTitle),
          findsOneWidget,
        );
        expect(
          find.text('Too many failed password attempts.'),
          findsOneWidget,
        );
        expect(
          find.textContaining('45 seconds'),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.securityStatusStandingRestricted),
          findsOneWidget,
        );

        // Tapping reset password navigates to ForgotPasswordScreen
        final resetBtn = find.byKey(const Key('lockoutResetPasswordButton'));
        await tester.ensureVisible(resetBtn);
        await tester.tap(resetBtn);
        await tester.pumpAndSettle();

        expect(find.byType(ForgotPasswordScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Confirmed lockout: tapping Back to Sign In navigates to LoginScreen',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(
              initialIsLockedOut: true,
              retryAfterSeconds: 30,
            ),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final signInBtn = find.byKey(const Key('lockoutSignInButton'));
        await tester.ensureVisible(signInBtn);
        await tester.tap(signInBtn);
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Rate-limited state via AuthService: renders rate-limit banner and retry guidance',
      (WidgetTester tester) async {
        AuthService.instance.setRateLimited(
          isLimited: true,
          retryAfterSeconds: 60,
          message: 'Backend rate limit exceeded. Please wait.',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('lockoutAlertBanner')), findsOneWidget);
        expect(
          find.text('Backend rate limit exceeded. Please wait.'),
          findsOneWidget,
        );
        expect(
          find.textContaining('60 seconds'),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Truthful empty events state: renders empty card and audit logging configuration pending notice',
      (WidgetTester tester) async {
        AuthService.instance.setSecurityAlertsDelegate(() async => []);

        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(
          find.byKey(const Key('securityEventsEmptyCard')),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.securityEventsEmptyTitle),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('auditConfigPendingCard')),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.securityEventsAuditPendingTitle),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Populated security events: renders events list with correct severity badges and read-only integrity',
      (WidgetTester tester) async {
        final mockAlerts = [
          SecurityAlert(
            id: 'evt_001',
            title: 'Multiple Failed Sign-In Attempts',
            description:
                '3 consecutive failed authentication attempts were detected.',
            severity: SecurityAlertSeverity.critical,
            timestamp: DateTime.utc(2026, 10, 14, 01, 30),
          ),
          SecurityAlert(
            id: 'evt_002',
            title: 'Account Password Updated',
            description:
                'Your account password was updated successfully via authenticated session.',
            severity: SecurityAlertSeverity.warning,
            timestamp: DateTime.utc(2026, 10, 14, 01, 15),
          ),
          SecurityAlert(
            id: 'evt_003',
            title: 'Two-Factor Authentication Active',
            description: 'TOTP authenticator app factor was verified.',
            severity: SecurityAlertSeverity.info,
            timestamp: DateTime.utc(2026, 10, 14, 01, 00),
          ),
        ];

        AuthService.instance.setSecurityAlertsDelegate(() async => mockAlerts);

        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(
          find.byKey(const Key('securityAlertItem_evt_001')),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('securityAlertItem_evt_002')),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('securityAlertItem_evt_003')),
          findsOneWidget,
        );

        expect(find.text(AppStrings.securityAlertSeverityCritical), findsOneWidget);
        expect(find.text(AppStrings.securityAlertSeverityWarning), findsOneWidget);
        expect(find.text(AppStrings.securityAlertSeverityInfo), findsOneWidget);

        // Security safeguard: Audit integrity is strictly preserved (no edit or delete actions)
        expect(find.byIcon(Icons.delete), findsNothing);
        expect(find.byIcon(Icons.edit), findsNothing);
      },
    );

    testWidgets(
      'Handles loading state and event refresh trigger',
      (WidgetTester tester) async {
        final completer = Completer<List<SecurityAlert>>();
        AuthService.instance.setSecurityAlertsDelegate(() => completer.future);

        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pump(); // start load frame

        expect(find.byKey(const Key('eventsLoadingIndicator')), findsOneWidget);

        completer.complete([]);
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('eventsLoadingIndicator')), findsNothing);
      },
    );

    testWidgets(
      'Handles event retrieval failure and renders error card with retry action',
      (WidgetTester tester) async {
        AuthService.instance.setSecurityAlertsDelegate(() async {
          throw Exception('Network error');
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('eventsErrorCard')), findsOneWidget);
        expect(
          find.text(AppStrings.securityEventsLoadError),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Quick action buttons navigate to 2FA and Change Password screens',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'user@example.com',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // 1. Two-factor action
        final twoFactorBtn = find.byKey(const Key('quickActionTwoFactorButton'));
        await tester.ensureVisible(twoFactorBtn);
        await tester.tap(twoFactorBtn);
        await tester.pumpAndSettle();

        expect(find.byType(TwoFactorAuthScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Quick action buttons navigate to Change Password screen',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'user@example.com',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final changePassBtn =
            find.byKey(const Key('quickActionChangePasswordButton'));
        await tester.ensureVisible(changePassBtn);
        await tester.tap(changePassBtn);
        await tester.pumpAndSettle();

        expect(find.byType(ChangePasswordScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Top back button and footer link navigate back to workspace or login',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'user@example.com',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final footerLink = find.byKey(const Key('footerBackLink'));
        await tester.ensureVisible(footerLink);
        await tester.tap(footerLink);
        await tester.pumpAndSettle();

        expect(find.byType(RoutePlaceholderScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Renders SecurityAlertsScreen without overflow across multiple device screen sizes',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        final screenSizes = [
          const Size(320, 568), // Small mobile
          const Size(390, 844), // Standard mobile
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const SecurityAlertsScreen(
                initialIsLockedOut: true,
                retryAfterSeconds: 30,
              ),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.text(AppStrings.securityAlertsHeading), findsOneWidget);
          expect(
            find.byKey(const Key('securitySummaryCard')),
            findsOneWidget,
          );
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons and elements support keyboard navigation and focus on Screen 018',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(SecurityAlertsScreen), findsOneWidget);
      },
    );
  });

  group('Screen 019 — Active Sessions & Devices Screen Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
    });

    tearDown(() {
      AuthService.instance.resetToDefault();
    });

    testWidgets(
      'Authenticated user: renders current session with truthful details and "This Device" badge',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'auditor@digitaltrust.ai',
          userId: 'usr_sec_99',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ActiveSessionsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.activeSessionsHeading), findsOneWidget);
        expect(find.byKey(const Key('currentSessionCard')), findsOneWidget);
        expect(find.byKey(const Key('currentSessionBadge')), findsOneWidget);
        expect(find.text(AppStrings.currentSessionBadge), findsOneWidget);
        expect(find.text('auditor@digitaltrust.ai'), findsOneWidget);
        expect(find.text('Active Now'), findsOneWidget);
      },
    );

    testWidgets(
      'Unauthenticated state: renders authentication required card and blocks access',
      (WidgetTester tester) async {
        AuthService.instance.resetToDefault();

        await tester.pumpWidget(
          MaterialApp(
            home: const ActiveSessionsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('unauthenticatedCard')), findsOneWidget);
        expect(
          find.text(AppStrings.activeSessionsUnauthenticatedTitle),
          findsOneWidget,
        );

        final signInBtn = find.byKey(const Key('signInButton'));
        await tester.tap(signInBtn);
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Sign-out confirmation dialog opens, cancels cleanly, and confirming triggers sign-out',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'admin@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ActiveSessionsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap sign-out on current device
        final signOutBtn =
            find.byKey(const Key('currentSessionSignOutButton'));
        await tester.ensureVisible(signOutBtn);
        await tester.tap(signOutBtn);
        await tester.pumpAndSettle();

        // Verify confirmation dialog is displayed
        expect(find.byKey(const Key('signOutConfirmDialog')), findsOneWidget);
        expect(find.text(AppStrings.signOutConfirmTitle), findsOneWidget);

        // Cancel dialog
        final cancelBtn = find.byKey(const Key('cancelSignOutButton'));
        await tester.tap(cancelBtn);
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('signOutConfirmDialog')), findsNothing);
        expect(AuthService.instance.hasAuthenticatedSession, isTrue);

        // Tap sign out again and confirm
        await tester.tap(signOutBtn);
        await tester.pumpAndSettle();

        final confirmBtn = find.byKey(const Key('confirmSignOutButton'));
        await tester.tap(confirmBtn);
        await tester.pumpAndSettle();

        expect(AuthService.instance.hasAuthenticatedSession, isFalse);
        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Truthful remote sessions limitation notice rendered when backend inventory is pending',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ActiveSessionsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Without multi-session backend extension, pending card is displayed
        expect(
          find.byKey(const Key('otherSessionsBackendPendingCard')),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.otherSessionsBackendPendingTitle),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Populated remote sessions: renders remote devices with distinct card and truthful details',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        AuthService.instance.setActiveSessionsDelegate(() async {
          return [
            AuthSessionInfo(
              id: 'sess_curr_1',
              deviceLabel: 'Chrome on macOS',
              clientType: 'Flutter Web',
              isCurrentSession: true,
              lastActive: DateTime.now(),
            ),
            AuthSessionInfo(
              id: 'sess_remote_2',
              deviceLabel: 'Safari on iPhone 15 Pro',
              clientType: 'Mobile Browser',
              ipAddress: '198.51.100.42',
              location: 'San Francisco, CA, USA',
              isCurrentSession: false,
              lastActive: DateTime.now(),
            ),
          ];
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ActiveSessionsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('currentSessionCard')), findsOneWidget);
        expect(
          find.byKey(const Key('remoteSessionCard_sess_remote_2')),
          findsOneWidget,
        );
        expect(find.text('Safari on iPhone 15 Pro'), findsOneWidget);
        expect(find.text('Mobile Browser'), findsOneWidget);
        expect(
          find.text('${AppStrings.sessionIpAddressLabel}198.51.100.42'),
          findsOneWidget,
        );
        expect(
          find.text('${AppStrings.sessionLocationLabel}San Francisco, CA, USA'),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('revokeSessionButton_sess_remote_2')),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Revoking remote session: requires confirmation dialog and cancels cleanly',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        AuthService.instance.setActiveSessionsDelegate(() async {
          return [
            AuthSessionInfo(
              id: 'sess_curr_1',
              deviceLabel: 'Chrome on macOS',
              clientType: 'Flutter Web',
              isCurrentSession: true,
            ),
            AuthSessionInfo(
              id: 'sess_remote_2',
              deviceLabel: 'Firefox on Linux',
              clientType: 'Desktop Browser',
              isCurrentSession: false,
            ),
          ];
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ActiveSessionsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final revokeBtn =
            find.byKey(const Key('revokeSessionButton_sess_remote_2'));
        await tester.ensureVisible(revokeBtn);
        await tester.tap(revokeBtn);
        await tester.pumpAndSettle();

        // Verify confirmation dialog
        expect(
          find.byKey(const Key('revokeConfirmDialog_sess_remote_2')),
          findsOneWidget,
        );

        // Cancel
        final cancelBtn = find.byKey(const Key('cancelRevokeButton'));
        await tester.tap(cancelBtn);
        await tester.pumpAndSettle();

        expect(
          find.byKey(const Key('revokeConfirmDialog_sess_remote_2')),
          findsNothing,
        );
      },
    );

    testWidgets(
      'Revoking remote session: confirming invokes backend delegate and shows success toast',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        var remoteSessions = [
          AuthSessionInfo(
            id: 'sess_curr_1',
            deviceLabel: 'Chrome on macOS',
            clientType: 'Flutter Web',
            isCurrentSession: true,
          ),
          AuthSessionInfo(
            id: 'sess_remote_2',
            deviceLabel: 'Firefox on Linux',
            clientType: 'Desktop Browser',
            isCurrentSession: false,
          ),
        ];

        AuthService.instance.setActiveSessionsDelegate(() async => remoteSessions);

        String? revokedIdReceived;
        AuthService.instance.setRevokeSessionDelegate(({required String sessionId}) async {
          revokedIdReceived = sessionId;
          remoteSessions = [remoteSessions.first];
          return AuthSessionRevocationResult.success();
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ActiveSessionsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final revokeBtn =
            find.byKey(const Key('revokeSessionButton_sess_remote_2'));
        await tester.ensureVisible(revokeBtn);
        await tester.tap(revokeBtn);
        await tester.pumpAndSettle();

        final confirmBtn = find.byKey(const Key('confirmRevokeButton'));
        await tester.tap(confirmBtn);
        await tester.pumpAndSettle();

        expect(revokedIdReceived, equals('sess_remote_2'));
        expect(find.text(AppStrings.revokeSessionSuccessToast), findsOneWidget);
      },
    );

    testWidgets(
      'Revoking remote session failure: displays honest error message without claiming revocation',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        AuthService.instance.setActiveSessionsDelegate(() async {
          return [
            AuthSessionInfo(
              id: 'sess_curr_1',
              deviceLabel: 'Chrome on macOS',
              clientType: 'Flutter Web',
              isCurrentSession: true,
            ),
            AuthSessionInfo(
              id: 'sess_remote_2',
              deviceLabel: 'Edge on Windows',
              clientType: 'Desktop Browser',
              isCurrentSession: false,
            ),
          ];
        });

        AuthService.instance.setRevokeSessionDelegate(({required String sessionId}) async {
          return AuthSessionRevocationResult.failure('Backend service unreachable.');
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ActiveSessionsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final revokeBtn =
            find.byKey(const Key('revokeSessionButton_sess_remote_2'));
        await tester.ensureVisible(revokeBtn);
        await tester.tap(revokeBtn);
        await tester.pumpAndSettle();

        final confirmBtn = find.byKey(const Key('confirmRevokeButton'));
        await tester.tap(confirmBtn);
        await tester.pumpAndSettle();

        expect(find.text('Backend service unreachable.'), findsOneWidget);
      },
    );

    testWidgets(
      'Handles loading error and allows retry',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        bool shouldFail = true;
        AuthService.instance.setActiveSessionsDelegate(() async {
          if (shouldFail) {
            throw Exception('Network connection timed out');
          }
          return [
            AuthSessionInfo(
              id: 'sess_curr_1',
              deviceLabel: 'Chrome on macOS',
              clientType: 'Flutter Web',
              isCurrentSession: true,
            ),
          ];
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ActiveSessionsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('sessionsLoadErrorCard')), findsOneWidget);
        expect(find.text(AppStrings.activeSessionsLoadError), findsOneWidget);

        // Fix error and retry
        shouldFail = false;
        final retryBtn = find.byKey(const Key('retryLoadSessionsButton'));
        await tester.tap(retryBtn);
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('currentSessionCard')), findsOneWidget);
        expect(find.byKey(const Key('sessionsLoadErrorCard')), findsNothing);
      },
    );

    testWidgets(
      'Refresh button reloads session list',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        int fetchCount = 0;
        AuthService.instance.setActiveSessionsDelegate(() async {
          fetchCount++;
          return [
            AuthSessionInfo(
              id: 'sess_curr_1',
              deviceLabel: 'Chrome on macOS',
              clientType: 'Flutter Web',
              isCurrentSession: true,
            ),
          ];
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const ActiveSessionsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(fetchCount, equals(1));

        final refreshBtn = find.byKey(const Key('refreshSessionsButton'));
        await tester.ensureVisible(refreshBtn);
        await tester.tap(refreshBtn);
        await tester.pumpAndSettle();

        expect(fetchCount, equals(2));
      },
    );

    testWidgets(
      'Top back button and footer links navigate cleanly to workspace or security alerts',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ActiveSessionsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final footerWorkspaceLink =
            find.byKey(const Key('footerWorkspaceLink'));
        await tester.ensureVisible(footerWorkspaceLink);
        await tester.tap(footerWorkspaceLink);
        await tester.pumpAndSettle();

        expect(find.byType(RoutePlaceholderScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Footer link navigates to Security Alerts screen',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ActiveSessionsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final footerSecurityLink =
            find.byKey(const Key('footerSecurityLink'));
        await tester.ensureVisible(footerSecurityLink);
        await tester.tap(footerSecurityLink);
        await tester.pumpAndSettle();

        expect(find.byType(SecurityAlertsScreen), findsOneWidget);
      },
    );

    testWidgets(
      'SecurityAlertsScreen quick action button navigates to ActiveSessionsScreen',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final activeSessionsBtn =
            find.byKey(const Key('quickActionActiveSessionsButton'));
        await tester.ensureVisible(activeSessionsBtn);
        await tester.tap(activeSessionsBtn);
        await tester.pumpAndSettle();

        expect(find.byType(ActiveSessionsScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Renders ActiveSessionsScreen without overflow across multiple device screen sizes',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        final screenSizes = [
          const Size(320, 568), // Small mobile
          const Size(390, 844), // Standard mobile
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const ActiveSessionsScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.text(AppStrings.activeSessionsHeading), findsOneWidget);
          expect(find.byKey(const Key('currentSessionCard')), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons and elements support keyboard navigation and focus on Screen 019',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ActiveSessionsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(ActiveSessionsScreen), findsOneWidget);
      },
    );
  });

  group('Screen 020 — Account Recovery & Backup Options Screen Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
    });

    tearDown(() {
      AuthService.instance.resetToDefault();
    });

    testWidgets(
      'Authenticated user: renders primary recovery email with truthful verified badge',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'recovery@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const AccountRecoveryScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.accountRecoveryHeading), findsOneWidget);
        expect(
          find.byKey(const Key('primaryRecoveryChannelCard')),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('recoveryEmailStatusBadge')),
          findsOneWidget,
        );
        expect(find.text(AppStrings.recoveryEmailStatusVerified), findsOneWidget);
        expect(find.text('recovery@digitaltrust.ai'), findsOneWidget);
      },
    );

    testWidgets(
      'Unauthenticated state: renders authentication required card and blocks access',
      (WidgetTester tester) async {
        AuthService.instance.resetToDefault();

        await tester.pumpWidget(
          MaterialApp(
            home: const AccountRecoveryScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('unauthenticatedCard')), findsOneWidget);
        expect(
          find.text(AppStrings.recoveryUnauthenticatedTitle),
          findsOneWidget,
        );

        final signInBtn = find.byKey(const Key('signInButton'));
        await tester.tap(signInBtn);
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Sending password reset recovery link: calls AuthService and shows success snackbar',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        String? resetEmailCalled;
        AuthService.instance.setResetPasswordDelegate(
          ({required String email, String? redirectTo}) async {
            resetEmailCalled = email;
            return AuthPasswordResetResult.success(email: email);
          },
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const AccountRecoveryScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final sendResetBtn = find.byKey(const Key('sendResetLinkButton'));
        await tester.ensureVisible(sendResetBtn);
        await tester.tap(sendResetBtn);
        await tester.pumpAndSettle();

        expect(resetEmailCalled, equals('officer@digitaltrust.ai'));
        expect(
          find.text(AppStrings.recoveryTestResetSuccess),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Link to Forgot Password flow navigates directly to ForgotPasswordScreen',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const AccountRecoveryScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final forgotPassBtn =
            find.byKey(const Key('goToForgotPasswordButton'));
        await tester.ensureVisible(forgotPassBtn);
        await tester.tap(forgotPassBtn);
        await tester.pumpAndSettle();

        expect(find.byType(ForgotPasswordScreen), findsOneWidget);
      },
    );

    testWidgets(
      'MFA Recovery card: renders correct status and navigates to TwoFactorAuthScreen',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
          mfaStatus: MfaStatus.enrolled,
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const AccountRecoveryScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('mfaRecoveryCard')), findsOneWidget);
        expect(find.text('Enabled (Protected)'), findsOneWidget);

        final manageMfaBtn = find.byKey(const Key('manageMfaButton'));
        await tester.ensureVisible(manageMfaBtn);
        await tester.tap(manageMfaBtn);
        await tester.pumpAndSettle();

        expect(find.byType(TwoFactorAuthScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Emergency Backup Codes card: renders truthful pending notice when not configured on backend',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const AccountRecoveryScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('backupCodesCard')), findsOneWidget);
        expect(
          find.byKey(const Key('backupCodesPendingNotice')),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.recoveryBackupCodesPendingTitle),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Emergency Backup Codes card: renders remaining codes count when configured by backend',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'admin@digitaltrust.ai',
        );

        AuthService.instance.setRecoveryStatusDelegate(() async {
          return const AuthRecoveryStatus(
            primaryEmail: 'admin@digitaltrust.ai',
            isEmailVerified: true,
            hasBackupCodesConfigured: true,
            remainingBackupCodesCount: 8,
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const AccountRecoveryScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.recoveryBackupCodesCountPrefix),
          findsOneWidget,
        );
        expect(find.text('8'), findsOneWidget);
      },
    );

    testWidgets(
      'Handles loading error and allows retry',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        bool shouldFail = true;
        AuthService.instance.setRecoveryStatusDelegate(() async {
          if (shouldFail) {
            throw Exception('Connection failed');
          }
          return const AuthRecoveryStatus(
            primaryEmail: 'officer@digitaltrust.ai',
            isEmailVerified: true,
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const AccountRecoveryScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('recoveryLoadErrorCard')), findsOneWidget);
        expect(find.text(AppStrings.recoveryLoadError), findsOneWidget);

        // Fix error and retry
        shouldFail = false;
        final retryBtn = find.byKey(const Key('retryLoadRecoveryButton'));
        await tester.tap(retryBtn);
        await tester.pumpAndSettle();

        expect(
          find.byKey(const Key('primaryRecoveryChannelCard')),
          findsOneWidget,
        );
        expect(find.byKey(const Key('recoveryLoadErrorCard')), findsNothing);
      },
    );

    testWidgets(
      'Refresh button reloads recovery status',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        int fetchCount = 0;
        AuthService.instance.setRecoveryStatusDelegate(() async {
          fetchCount++;
          return const AuthRecoveryStatus(
            primaryEmail: 'officer@digitaltrust.ai',
            isEmailVerified: true,
          );
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const AccountRecoveryScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(fetchCount, equals(1));

        final refreshBtn = find.byKey(const Key('refreshRecoveryButton'));
        await tester.ensureVisible(refreshBtn);
        await tester.tap(refreshBtn);
        await tester.pumpAndSettle();

        expect(fetchCount, equals(2));
      },
    );

    testWidgets(
      'Top back button and footer links navigate cleanly to workspace or security alerts',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const AccountRecoveryScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final footerWorkspaceLink =
            find.byKey(const Key('footerWorkspaceLink'));
        await tester.ensureVisible(footerWorkspaceLink);
        await tester.tap(footerWorkspaceLink);
        await tester.pumpAndSettle();

        expect(find.byType(RoutePlaceholderScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Footer link navigates to Security Alerts screen',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const AccountRecoveryScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final footerSecurityLink =
            find.byKey(const Key('footerSecurityLink'));
        await tester.ensureVisible(footerSecurityLink);
        await tester.tap(footerSecurityLink);
        await tester.pumpAndSettle();

        expect(find.byType(SecurityAlertsScreen), findsOneWidget);
      },
    );

    testWidgets(
      'SecurityAlertsScreen quick action button navigates to AccountRecoveryScreen',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const SecurityAlertsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final accountRecoveryBtn =
            find.byKey(const Key('quickActionAccountRecoveryButton'));
        await tester.ensureVisible(accountRecoveryBtn);
        await tester.tap(accountRecoveryBtn);
        await tester.pumpAndSettle();

        expect(find.byType(AccountRecoveryScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Renders AccountRecoveryScreen without overflow across multiple device screen sizes',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        final screenSizes = [
          const Size(320, 568), // Small mobile
          const Size(390, 844), // Standard mobile
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const AccountRecoveryScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.text(AppStrings.accountRecoveryHeading), findsOneWidget);
          expect(
            find.byKey(const Key('primaryRecoveryChannelCard')),
            findsOneWidget,
          );
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons and elements support keyboard navigation and focus on Screen 020',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const AccountRecoveryScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(AccountRecoveryScreen), findsOneWidget);
      },
    );
  });

  group('Screen 021 — User Dashboard Screen Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
      UserTypeController.instance.resetToDefault();
      LocationPreferencesController.instance.resetToDefault();
    });

    tearDown(() {
      AuthService.instance.resetToDefault();
      UserTypeController.instance.resetToDefault();
      LocationPreferencesController.instance.resetToDefault();
    });

    testWidgets(
      'Authenticated user with name: renders welcome message, email, role badge, and dashboard cards',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'sarah.connor@cyberdyne.org',
          userName: 'Sarah Connor',
        );
        UserTypeController.instance.selectUserType(UserType.individual);

        await tester.pumpWidget(
          MaterialApp(
            home: const UserDashboardScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(
          find.text('${AppStrings.dashboardWelcomeHeading}, Sarah Connor'),
          findsOneWidget,
        );
        expect(find.text('sarah.connor@cyberdyne.org'), findsWidgets);
        expect(find.byKey(const Key('dashboardUserTypeBadge')), findsOneWidget);
        expect(
          find.byKey(const Key('verificationOverviewCard')),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('profileCompletionCard')),
          findsOneWidget,
        );
        expect(find.byKey(const Key('pendingActionsCard')), findsOneWidget);
        expect(find.byKey(const Key('quickActionsGrid')), findsOneWidget);
        expect(find.byKey(const Key('recentActivityCard')), findsOneWidget);
      },
    );

    testWidgets(
      'Authenticated user without name: renders default welcome heading',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'analyst@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserDashboardScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text(AppStrings.dashboardWelcomeHeading), findsOneWidget);
        expect(find.text('analyst@digitaltrust.ai'), findsWidgets);
      },
    );

    testWidgets(
      'Unauthenticated state: renders security barrier card and blocks dashboard access',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const UserDashboardScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(
          find.byKey(const Key('dashboardUnauthenticatedCard')),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.dashboardUnauthenticatedTitle),
          findsOneWidget,
        );
        expect(find.byKey(const Key('dashboardSignInButton')), findsOneWidget);
        expect(find.byKey(const Key('verificationOverviewCard')), findsNothing);
      },
    );

    testWidgets(
      'Tapping sign in button on unauthenticated barrier navigates to LoginScreen',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const UserDashboardScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final signInBtn = find.byKey(const Key('dashboardSignInButton'));
        expect(signInBtn, findsOneWidget);
        await tester.tap(signInBtn);
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Truthful Verification Overview: renders Not Started status with distinction banner',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'citizen@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserDashboardScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.dashboardIdentityNotStarted),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.dashboardAccountEmailVerified),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('identityVerificationActionButton')),
          findsOneWidget,
        );
        expect(
          find.descendant(
            of: find.byKey(const Key('identityVerificationActionButton')),
            matching: find.text(AppStrings.dashboardStartVerificationButton),
          ),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Truthful Verification Overview: renders In Progress, Action Required, and Completed statuses',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'citizen@digitaltrust.ai',
        );

        // 1. In Progress
        AuthService.instance.setVerificationOverviewDelegate(
          () async => const IdentityVerificationOverview(
            status: IdentityVerificationStatus.inProgress,
          ),
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserDashboardScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.dashboardIdentityInProgress),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.dashboardReviewVerificationButton),
          findsOneWidget,
        );

        // 2. Action Required
        AuthService.instance.setVerificationOverviewDelegate(
          () async => const IdentityVerificationOverview(
            status: IdentityVerificationStatus.actionRequired,
            actionRequiredReason: 'Passport image blurred. Please re-upload.',
          ),
        );

        final refreshBtn = find.byKey(const Key('dashboardRefreshButton'));
        await tester.tap(refreshBtn);
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.dashboardIdentityActionRequired),
          findsOneWidget,
        );
        expect(
          find.text('Passport image blurred. Please re-upload.'),
          findsOneWidget,
        );
        expect(
          find.descendant(
            of: find.byKey(const Key('identityVerificationActionButton')),
            matching: find.text(AppStrings.dashboardResolveActionButton),
          ),
          findsOneWidget,
        );

        // 3. Completed
        AuthService.instance.setVerificationOverviewDelegate(
          () async => const IdentityVerificationOverview(
            status: IdentityVerificationStatus.completed,
          ),
        );

        await tester.tap(refreshBtn);
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.dashboardIdentityCompleted),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Profile Completion Gauge calculates strictly based on defined, real fields',
      (WidgetTester tester) async {
        LocationPreferencesController.instance.clearSelection();
        // Step 1: Only email verified -> 20%
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'user1@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserDashboardScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text('20%'), findsOneWidget);

        // Step 2: Name added -> 40%
        AuthService.instance.updateUserName('John Matrix');
        await tester.pumpAndSettle();

        expect(find.text('40%'), findsOneWidget);

        // Step 3: Location added -> 60%
        LocationPreferencesController.instance.saveLocation(
          CountryRegionData.defaultSuggestedCountry,
          null,
        );
        await tester.pumpAndSettle();

        expect(find.text('60%'), findsOneWidget);

        // Step 4: User type added -> 80%
        UserTypeController.instance.selectUserType(UserType.individual);
        await tester.pumpAndSettle();

        expect(find.text('80%'), findsOneWidget);

        // Step 5: MFA enrolled -> 100%
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'user1@digitaltrust.ai',
          userName: 'John Matrix',
          mfaStatus: MfaStatus.enrolled,
        );
        await tester.pumpAndSettle();

        expect(find.text('100%'), findsOneWidget);
      },
    );

    testWidgets(
      'Pending Actions displays honest checklist and transitions to All Caught Up',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'user2@digitaltrust.ai',
        );
        LocationPreferencesController.instance.clearSelection();

        await tester.pumpWidget(
          MaterialApp(
            home: const UserDashboardScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(
          find.byKey(const Key('pendingActionStartKycButton')),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('pendingActionEnableMfaButton')),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('pendingActionSetLocationButton')),
          findsOneWidget,
        );

        // Mark all items as satisfied
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'user2@digitaltrust.ai',
          userName: 'Sarah Connor',
          mfaStatus: MfaStatus.enrolled,
        );
        AuthService.instance.setVerificationOverviewDelegate(
          () async => const IdentityVerificationOverview(
            status: IdentityVerificationStatus.completed,
          ),
        );
        LocationPreferencesController.instance.saveLocation(
          CountryRegionData.defaultSuggestedCountry,
          null,
        );

        final refreshBtn = find.byKey(const Key('dashboardRefreshButton'));
        await tester.tap(refreshBtn);
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('pendingActionsCard')), findsOneWidget);
      },
    );

    testWidgets(
      'Quick Actions Grid triggers navigation to respective destinations',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'user3@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserDashboardScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('quickActionStartKyc')), findsOneWidget);
        expect(find.byKey(const Key('quickActionDocuments')), findsOneWidget);
        expect(find.byKey(const Key('quickActionProfile')), findsOneWidget);
        expect(find.byKey(const Key('quickActionSecurity')), findsOneWidget);
        expect(find.byKey(const Key('quickActionHistory')), findsOneWidget);

        // Tap Security Settings
        final securityBtn = find.byKey(const Key('quickActionSecurity'));
        await tester.ensureVisible(securityBtn);
        await tester.tap(securityBtn);
        await tester.pumpAndSettle();

        expect(find.byType(SecurityAlertsScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Recent Activity displays alerts when available and empty notice when none',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'auditor@digitaltrust.ai',
        );

        // 1. Empty state
        AuthService.instance.setSecurityAlertsDelegate(() async => []);

        await tester.pumpWidget(
          MaterialApp(
            home: const UserDashboardScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(
          find.byKey(const Key('recentActivityEmptyState')),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.dashboardRecentActivityEmpty),
          findsOneWidget,
        );

        // 2. Populated alerts
        AuthService.instance.setSecurityAlertsDelegate(
          () async => [
            SecurityAlert(
              id: 'ev_001',
              title: 'Successful Authentication',
              description: 'Sign-in confirmed from verified Chrome browser.',
              severity: SecurityAlertSeverity.info,
              timestamp: DateTime.now().subtract(const Duration(minutes: 5)),
            ),
          ],
        );

        final refreshBtn = find.byKey(const Key('dashboardRefreshButton'));
        await tester.tap(refreshBtn);
        await tester.pumpAndSettle();

        expect(find.text('Successful Authentication'), findsOneWidget);
      },
    );

    testWidgets(
      'Sign out dialog confirms, cancels cleanly, and terminates session on confirm',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserDashboardScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final signOutBtn = find.byKey(const Key('dashboardSignOutButton'));
        await tester.tap(signOutBtn);
        await tester.pumpAndSettle();

        expect(
          find.text(AppStrings.dashboardSignOutConfirmTitle),
          findsOneWidget,
        );

        // Cancel
        final cancelBtn = find.byKey(const Key('dashboardSignOutCancelButton'));
        await tester.tap(cancelBtn);
        await tester.pumpAndSettle();

        expect(AuthService.instance.hasAuthenticatedSession, isTrue);

        // Open dialog again and Confirm
        await tester.tap(signOutBtn);
        await tester.pumpAndSettle();

        final confirmBtn =
            find.byKey(const Key('dashboardSignOutConfirmButton'));
        await tester.tap(confirmBtn);
        await tester.pumpAndSettle();

        expect(AuthService.instance.hasAuthenticatedSession, isFalse);
        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Renders UserDashboardScreen without overflow across multiple device screen sizes',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
          userName: 'Chief Trust Officer',
        );

        final screenSizes = [
          const Size(320, 568), // Small mobile
          const Size(390, 844), // Standard mobile
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const UserDashboardScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.text(AppStrings.dashboardHeading), findsOneWidget);
          expect(
            find.byKey(const Key('verificationOverviewCard')),
            findsOneWidget,
          );
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Action buttons and elements support keyboard navigation and focus on Screen 021',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'officer@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserDashboardScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Send Tab keys to traverse focusable elements
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(UserDashboardScreen), findsOneWidget);
      },
    );
  });

  group('Screen 022 — User Profile Overview Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
      LocationPreferencesController.instance.resetToDefault();
      UserTypeController.instance.resetToDefault();
      PurposeSelectionController.instance.resetToDefault();
    });

    testWidgets(
      'Authenticated user with complete profile: renders header, avatar initials, email, badges, and all sections',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'sarah.connor@cyberdyne.io',
          userName: 'Sarah Connor',
          userId: 'usr_sarah_007',
          mfaStatus: MfaStatus.enrolled,
        );
        UserTypeController.instance.selectUserType(UserType.individual);
        LocationPreferencesController.instance.saveLocation(
          CountryRegionData.defaultSuggestedCountry,
          null,
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserProfileOverviewScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // 1. Verify Page Title and Subtitle
        expect(find.byKey(const Key('profileScreenTitle')), findsOneWidget);
        expect(find.text(AppStrings.profileHeading), findsOneWidget);
        expect(find.text(AppStrings.profileSubtitle), findsOneWidget);

        // 2. Avatar with initials
        expect(find.byKey(const Key('profileAvatarPlaceholder')), findsOneWidget);
        expect(find.byKey(const Key('profileAvatarInitials')), findsOneWidget);
        expect(find.text('SC'), findsOneWidget);

        // 3. User display name & email
        expect(find.text('Sarah Connor'), findsWidgets);
        expect(find.text('sarah.connor@cyberdyne.io'), findsWidgets);

        // 4. Badges
        expect(find.byKey(const Key('profileRoleBadge')), findsOneWidget);
        expect(find.byKey(const Key('profileEmailVerifiedBadge')), findsOneWidget);
        expect(find.text('Email Verified'), findsOneWidget);
        expect(find.byKey(const Key('profileUserIdBadge')), findsOneWidget);

        // 5. Main Action Buttons
        expect(find.byKey(const Key('editProfileButton')), findsOneWidget);
        expect(find.byKey(const Key('securitySettingsButton')), findsOneWidget);
        expect(find.byKey(const Key('refreshProfileButton')), findsOneWidget);

        // 6. Transparent storage notice
        expect(find.byKey(const Key('profileStorageNoticeText')), findsOneWidget);
        expect(find.text(AppStrings.profileStorageNotice), findsOneWidget);

        // 7. Verify Sections
        expect(find.byKey(const Key('basicInformationCard')), findsOneWidget);
        expect(find.byKey(const Key('contactInformationCard')), findsOneWidget);
        expect(find.byKey(const Key('accountStatusCard')), findsOneWidget);
        expect(find.byKey(const Key('profileCompletionCard')), findsOneWidget);
        expect(find.byKey(const Key('verificationOverviewCard')), findsOneWidget);
      },
    );

    testWidgets(
      'Authenticated user with minimal profile (no name, no location): renders honest unconfigured placeholders',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'anon@cyberdyne.io',
        );
        LocationPreferencesController.instance.clearSelection();

        await tester.pumpWidget(
          MaterialApp(
            home: const UserProfileOverviewScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Avatar fallback icon
        expect(find.byKey(const Key('profileAvatarDefaultIcon')), findsOneWidget);
        expect(find.byKey(const Key('profileAvatarInitials')), findsNothing);

        // Honest no name notice
        expect(find.text(AppStrings.profileNoNameProvided), findsWidgets);

        // Honest unconfigured location
        expect(find.text(AppStrings.profileNotSet), findsWidgets);
      },
    );

    testWidgets(
      'Unauthenticated state: renders security barrier card and redirects to sign in',
      (WidgetTester tester) async {
        // AuthService has no session
        await tester.pumpWidget(
          MaterialApp(
            home: const UserProfileOverviewScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('unauthenticatedCard')), findsOneWidget);
        expect(find.text(AppStrings.profileUnauthenticatedTitle), findsOneWidget);
        expect(find.byKey(const Key('profileSignInButton')), findsOneWidget);

        await tester.tap(find.byKey(const Key('profileSignInButton')));
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Distinction between Account/Email verification and Identity Verification is explicitly enforced',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'auditor@cyberdyne.io',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserProfileOverviewScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Email is verified (account sign-in active)
        expect(find.text('Email Verified'), findsOneWidget);

        // BUT Identity Verification is Not Started
        expect(find.text(AppStrings.dashboardIdentityNotStarted), findsOneWidget);

        // Distinction banner is rendered
        expect(find.byKey(const Key('verificationDistinctionBanner')), findsOneWidget);
        expect(find.text(AppStrings.profileIdentityDistinctionNotice), findsOneWidget);

        // Confidentiality notice is rendered
        expect(find.byKey(const Key('profileSensitiveDataNoticeText')), findsOneWidget);
        expect(find.text(AppStrings.profileSensitiveDataNotice), findsOneWidget);

        // Action button navigates to identity verification route
        final actionBtn = find.byKey(const Key('verificationActionButton'));
        await tester.ensureVisible(actionBtn);
        await tester.tap(actionBtn);
        await tester.pumpAndSettle();

        expect(find.byType(VerificationStatusScreen), findsOneWidget);
        expect(find.text(AppStrings.verificationStatusHeading), findsWidgets);
      },
    );

    testWidgets(
      'Profile Completion indicator calculates strictly based on defined, real fields',
      (WidgetTester tester) async {
        LocationPreferencesController.instance.clearSelection();
        // Step 1: Only email verified -> 20%
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'user@digitaltrust.ai',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserProfileOverviewScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text('20%'), findsOneWidget);

        // Step 2: Name added -> 40%
        AuthService.instance.updateUserName('John Matrix');
        await tester.pumpAndSettle();

        expect(find.text('40%'), findsOneWidget);

        // Step 3: Location added -> 60%
        LocationPreferencesController.instance.saveLocation(
          CountryRegionData.defaultSuggestedCountry,
          null,
        );
        await tester.pumpAndSettle();

        expect(find.text('60%'), findsOneWidget);

        // Step 4: User type added -> 80%
        UserTypeController.instance.selectUserType(UserType.individual);
        await tester.pumpAndSettle();

        expect(find.text('80%'), findsOneWidget);

        // Step 5: MFA enrolled -> 100%
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'user@digitaltrust.ai',
          userName: 'John Matrix',
          mfaStatus: MfaStatus.enrolled,
        );
        await tester.pumpAndSettle();

        expect(find.text('100%'), findsOneWidget);
      },
    );

    testWidgets(
      'Edit Profile button opens dialog, updates full name, and displays snackbar',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'agent@digitaltrust.ai',
          userName: 'Old Name',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserProfileOverviewScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.text('Old Name'), findsWidgets);

        // Tap Edit Profile
        final editBtn = find.byKey(const Key('editProfileButton'));
        await tester.tap(editBtn);
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('profileEditDialog')), findsOneWidget);
        expect(find.byKey(const Key('profileEditNameField')), findsOneWidget);

        // Enter new name
        await tester.enterText(
          find.byKey(const Key('profileEditNameField')),
          'Major Alan Schaefer',
        );
        await tester.pumpAndSettle();

        // Save
        final saveBtn = find.byKey(const Key('saveProfileEditButton'));
        await tester.tap(saveBtn);
        await tester.pumpAndSettle();

        // Verify Dialog closed and name updated
        expect(find.byKey(const Key('profileEditDialog')), findsNothing);
        expect(find.text('Major Alan Schaefer'), findsWidgets);
        expect(AuthService.instance.currentUserName, 'Major Alan Schaefer');
      },
    );

    testWidgets(
      'Security Settings button triggers navigation to AppRoutes.securityAlerts',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'security.admin@cyberdyne.io',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserProfileOverviewScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final secBtn = find.byKey(const Key('securitySettingsButton'));
        await tester.tap(secBtn);
        await tester.pumpAndSettle();

        expect(find.byType(SecurityAlertsScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Error state renders retry banner and recovers on retry tap',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'tester@cyberdyne.io',
        );

        // Cause error
        AuthService.instance.setVerificationOverviewDelegate(
          () async => throw Exception('Supabase connection lost'),
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserProfileOverviewScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('profileErrorBanner')), findsOneWidget);
        expect(find.text(AppStrings.profileLoadError), findsOneWidget);

        // Fix delegate and retry
        AuthService.instance.setVerificationOverviewDelegate(
          () async => const IdentityVerificationOverview(
            status: IdentityVerificationStatus.inProgress,
          ),
        );

        final retryBtn = find.byKey(const Key('profileRetryButton'));
        await tester.tap(retryBtn);
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('profileErrorBanner')), findsNothing);
        expect(find.text(AppStrings.dashboardIdentityInProgress), findsOneWidget);
      },
    );

    testWidgets(
      'Renders UserProfileOverviewScreen without overflow across mobile, tablet, and desktop',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'responsive@digitaltrust.ai',
          userName: 'Responsive User',
        );

        final screenSizes = [
          const Size(320, 568), // Small mobile
          const Size(390, 844), // Standard mobile
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const UserProfileOverviewScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.byKey(const Key('profileScreenTitle')), findsOneWidget);
          expect(find.byKey(const Key('profileHeaderCard')), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Supports keyboard navigation and focus on interactive elements',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'keyboard.user@digitaltrust.ai',
          userName: 'Keyboard Master',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserProfileOverviewScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pumpAndSettle();

        expect(find.byType(UserProfileOverviewScreen), findsOneWidget);
      },
    );
  });

  group('Screen 023 — Edit Personal Information Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
      LocationPreferencesController.instance.resetToDefault();
      UserTypeController.instance.resetToDefault();
      PurposeSelectionController.instance.resetToDefault();
    });

    testWidgets(
      'Authenticated user: prepopulates full name and location preferences and displays read-only security fields',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'alex.chen@cyberdyne.io',
          userName: 'Alex Chen',
          userId: 'usr_alex_001',
        );
        UserTypeController.instance.selectUserType(UserType.individual);
        LocationPreferencesController.instance.saveLocation(
          CountryRegionData.defaultSuggestedCountry,
          CountryRegionData.defaultSuggestedCountry.regions.first,
        );

        tester.view.physicalSize = const Size(1200, 1000);
        tester.view.devicePixelRatio = 1.0;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        await tester.pumpWidget(
          MaterialApp(
            home: const EditPersonalInformationScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // 1. Verify Page Title & Subtitle
        expect(find.byKey(const Key('editProfileHeading')), findsOneWidget);
        expect(find.text(AppStrings.editProfileHeading), findsOneWidget);
        expect(find.text(AppStrings.editProfileSubtitle), findsOneWidget);

        // 2. Prepopulated Name
        expect(find.byKey(const Key('editProfileNameField')), findsOneWidget);
        expect(find.text('Alex Chen'), findsWidgets);

        // 3. Prepopulated Country & Region
        expect(find.byKey(const Key('editProfileCountryDropdown')), findsOneWidget);
        expect(find.textContaining('India'), findsWidgets);

        // 4. Phone input and transparent pending note
        expect(find.byKey(const Key('editProfilePhoneField')), findsOneWidget);
        expect(find.byKey(const Key('editProfilePhoneNoteText')), findsOneWidget);
        expect(find.text(AppStrings.editProfilePhoneNote), findsOneWidget);

        // 5. Read-only Security and Guardrail items with honest explanations
        expect(find.byKey(const Key('readOnlyEmailItem')), findsOneWidget);
        expect(
          find.descendant(
            of: find.byKey(const Key('readOnlyEmailItem')),
            matching: find.text('alex.chen@cyberdyne.io'),
          ),
          findsOneWidget,
        );
        expect(find.text(AppStrings.editProfileEmailNote), findsOneWidget);

        expect(find.byKey(const Key('readOnlyAccountIdItem')), findsOneWidget);
        expect(
          find.descendant(
            of: find.byKey(const Key('readOnlyAccountIdItem')),
            matching: find.text('usr_alex_001'),
          ),
          findsOneWidget,
        );
        expect(find.text(AppStrings.editProfileAccountIdNote), findsOneWidget);

        expect(find.byKey(const Key('readOnlyRoleItem')), findsOneWidget);
        expect(
          find.descendant(
            of: find.byKey(const Key('readOnlyRoleItem')),
            matching: find.text('Individual'),
          ),
          findsOneWidget,
        );
        expect(find.text(AppStrings.editProfileRoleNote), findsOneWidget);

        // 6. Action buttons
        expect(find.byKey(const Key('cancelEditProfileButton')), findsOneWidget);
        expect(find.byKey(const Key('savePersonalInformationButton')), findsOneWidget);
      },
    );

    testWidgets(
      'Validation: empty name, short name, and invalid characters show appropriate validation errors',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'test@digitaltrust.ai',
          userName: 'Valid Name',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const EditPersonalInformationScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final nameField = find.byKey(const Key('editProfileNameField'));
        final saveBtn = find.byKey(const Key('savePersonalInformationButton'));

        // 1. Empty name
        await tester.enterText(nameField, '   ');
        await tester.ensureVisible(saveBtn);
        await tester.tap(saveBtn);
        await tester.pumpAndSettle();
        expect(find.text(AppStrings.editProfileNameRequiredError), findsOneWidget);

        // 2. Name too short (< 2 characters)
        await tester.enterText(nameField, 'A');
        await tester.ensureVisible(saveBtn);
        await tester.tap(saveBtn);
        await tester.pumpAndSettle();
        expect(find.text(AppStrings.editProfileNameLengthError), findsOneWidget);

        // 3. Name with illegal symbols
        await tester.enterText(nameField, 'Alex_99#');
        await tester.ensureVisible(saveBtn);
        await tester.tap(saveBtn);
        await tester.pumpAndSettle();
        expect(find.text(AppStrings.editProfileNameInvalidError), findsOneWidget);
      },
    );

    testWidgets(
      'Unsaved changes protection: editing field marks form dirty and triggers discard dialog on cancel',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'alex@cyberdyne.io',
          userName: 'Alex Original',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const EditPersonalInformationScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Initially clean: cancel pops without dialog
        final cancelBtn = find.byKey(const Key('cancelEditProfileButton'));

        // Make form dirty
        final nameField = find.byKey(const Key('editProfileNameField'));
        await tester.enterText(nameField, 'Alex Modified');
        await tester.pumpAndSettle();

        // Tap Cancel while dirty
        await tester.ensureVisible(cancelBtn);
        await tester.tap(cancelBtn);
        await tester.pumpAndSettle();

        // Verify Discard Changes Dialog is shown
        expect(find.byKey(const Key('discardChangesDialog')), findsOneWidget);
        expect(find.text(AppStrings.editProfileDiscardDialogTitle), findsOneWidget);
        expect(find.text(AppStrings.editProfileDiscardDialogDesc), findsOneWidget);

        // Tap "Keep Editing"
        await tester.tap(find.byKey(const Key('keepEditingButton')));
        await tester.pumpAndSettle();

        // Dialog dismissed, still on edit screen
        expect(find.byKey(const Key('discardChangesDialog')), findsNothing);
        expect(find.byKey(const Key('editProfileHeading')), findsOneWidget);

        // Tap Cancel again and confirm discard
        await tester.ensureVisible(cancelBtn);
        await tester.tap(cancelBtn);
        await tester.pumpAndSettle();
        expect(find.byKey(const Key('discardChangesDialog')), findsOneWidget);

        await tester.tap(find.byKey(const Key('confirmDiscardButton')));
        await tester.pumpAndSettle();

        // Dialog dismissed
        expect(find.byKey(const Key('discardChangesDialog')), findsNothing);
      },
    );

    testWidgets(
      'Successful profile update: validates input, updates AuthService and LocationPreferencesController, and shows success snackbar',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'clara.oswald@digitaltrust.ai',
          userName: 'Clara',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const EditPersonalInformationScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final nameField = find.byKey(const Key('editProfileNameField'));
        await tester.enterText(nameField, 'Clara Oswald');
        await tester.pumpAndSettle();

        final saveBtn = find.byKey(const Key('savePersonalInformationButton'));
        await tester.ensureVisible(saveBtn);
        await tester.tap(saveBtn);
        await tester.pumpAndSettle();

        // Verify updated state
        expect(AuthService.instance.currentUserName, 'Clara Oswald');
        expect(find.byKey(const Key('editProfileSuccessSnackBar')), findsOneWidget);
        expect(find.text(AppStrings.editProfileSuccessMessage), findsOneWidget);
      },
    );

    testWidgets(
      'Unauthenticated state: renders security barrier card and redirects to sign in',
      (WidgetTester tester) async {
        // No session
        await tester.pumpWidget(
          MaterialApp(
            home: const EditPersonalInformationScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('unauthenticatedCard')), findsOneWidget);
        expect(find.text(AppStrings.profileUnauthenticatedTitle), findsOneWidget);
        expect(find.byKey(const Key('editProfileSignInButton')), findsOneWidget);

        await tester.tap(find.byKey(const Key('editProfileSignInButton')));
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Error handling: displays error banner when update fails and recovers gracefully',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'error.test@digitaltrust.ai',
          userName: 'Original Name',
        );

        // Inject simulated backend error
        AuthService.instance.setUpdateProfileDelegate(
          ({required fullName, newEmail}) async => AuthProfileUpdateResult.failure(
            'Row Level Security policy rejected update. Unauthorized user session.',
          ),
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const EditPersonalInformationScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final nameField = find.byKey(const Key('editProfileNameField'));
        await tester.enterText(nameField, 'Attempted Name');
        await tester.pumpAndSettle();

        final saveBtn = find.byKey(const Key('savePersonalInformationButton'));
        await tester.ensureVisible(saveBtn);
        await tester.tap(saveBtn);
        await tester.pumpAndSettle();

        // Verify error banner is rendered
        final errorBanner = find.byKey(const Key('editProfileErrorBanner'));
        await tester.ensureVisible(errorBanner);
        expect(errorBanner, findsOneWidget);
        expect(
          find.text('Row Level Security policy rejected update. Unauthorized user session.'),
          findsOneWidget,
        );

        // Reset delegate and retry successfully
        AuthService.instance.setUpdateProfileDelegate(null);
        await tester.ensureVisible(saveBtn);
        await tester.tap(saveBtn);
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('editProfileErrorBanner')), findsNothing);
        expect(find.byKey(const Key('editProfileSuccessSnackBar')), findsOneWidget);
      },
    );

    testWidgets(
      'Responsive rendering across mobile to desktop sizes without layout overflow',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'responsive@digitaltrust.ai',
          userName: 'Dr. John Watson',
        );

        final screenSizes = [
          const Size(320, 568),  // Small mobile
          const Size(390, 844),  // Standard mobile
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const EditPersonalInformationScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.byKey(const Key('editProfileHeading')), findsOneWidget);
          expect(find.byKey(const Key('savePersonalInformationButton')), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );
  });

  group('Screen 024 — Profile Photo Management Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
    });

    tearDown(() {
      AuthService.instance.resetToDefault();
    });

    testWidgets(
      'Authenticated user without custom photo: renders current section with neutral initials avatar and privacy guidelines',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'maya.lin@digitaltrust.ai',
          userName: 'Maya Lin',
          userId: 'usr_maya_77',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ProfilePhotoScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Heading & navigation
        expect(find.byKey(const Key('profilePhotoHeading')), findsOneWidget);
        expect(find.text(AppStrings.photoHeading), findsOneWidget);
        expect(find.text(AppStrings.photoSubtitle), findsOneWidget);
        expect(find.byKey(const Key('profilePhotoBackButton')), findsOneWidget);

        // Current photo card
        expect(find.byKey(const Key('currentPhotoCard')), findsOneWidget);
        expect(find.byKey(const Key('neutralPhotoAvatarPlaceholder')), findsOneWidget);
        expect(find.byKey(const Key('neutralPhotoAvatarInitials')), findsOneWidget);
        expect(find.text('ML'), findsOneWidget);

        // Upload button exists and shows "Upload Photo"
        expect(find.byKey(const Key('uploadPhotoButton')), findsOneWidget);
        expect(find.text(AppStrings.photoUploadAction), findsOneWidget);

        // Remove button does NOT exist when no photo is set
        expect(find.byKey(const Key('removePhotoButton')), findsNothing);

        // Sample selection dropzone
        expect(find.byKey(const Key('photoDropZonePlaceholder')), findsOneWidget);
        expect(find.byKey(const Key('selectPngSampleButton')), findsOneWidget);
        expect(find.byKey(const Key('selectJpegSampleButton')), findsOneWidget);
        expect(find.byKey(const Key('selectWebpSampleButton')), findsOneWidget);

        // Privacy standards & badges
        expect(find.byKey(const Key('photoGuidelinesCard')), findsOneWidget);
        expect(find.byKey(const Key('privateBucketBadge')), findsOneWidget);
        expect(find.byKey(const Key('ownerOnlyRlsBadge')), findsOneWidget);
        expect(find.byKey(const Key('signedUrlExpiryBadge')), findsOneWidget);
        expect(find.text(AppStrings.photoGuideline1), findsOneWidget);
        expect(find.text(AppStrings.photoGuideline2), findsOneWidget);
      },
    );

    testWidgets(
      'Authenticated user with custom photo: displays image, Change Photo button, and Remove Photo button',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'maya.lin@digitaltrust.ai',
          userName: 'Maya Lin',
          userId: 'usr_maya_77',
        );

        // Set existing photo with valid PNG bytes
        final sampleBytes = Uint8List.fromList([
          0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
          0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
          0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00,
          0x0A, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
          0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49,
          0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
        ]);
        AuthService.instance.setProfilePhotoForTesting(
          filePath: 'usr_maya_77/avatar.png',
          bytes: sampleBytes,
          signedUrl: 'https://storage.supabase.co/profile-photos/usr_maya_77/avatar.png?token=signed123',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ProfilePhotoScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Verifies Image.memory is rendered and neutral placeholder is gone
        expect(find.byKey(const Key('currentPhotoMemoryImage')), findsOneWidget);
        expect(find.byKey(const Key('neutralPhotoAvatarPlaceholder')), findsNothing);

        // Action buttons
        expect(find.byKey(const Key('uploadPhotoButton')), findsOneWidget);
        expect(find.text(AppStrings.photoChangeAction), findsOneWidget);
        expect(find.byKey(const Key('removePhotoButton')), findsOneWidget);
        expect(find.text(AppStrings.photoRemoveAction), findsOneWidget);
      },
    );

    testWidgets(
      'Strict file validation: rejects corrupt/empty bytes, oversized file (>5MB), and invalid magic bytes',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'validator@digitaltrust.ai',
          userName: 'Validator Agent',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ProfilePhotoScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final screenState =
            tester.state<ProfilePhotoScreenState>(find.byType(ProfilePhotoScreen));

        // 1. Empty buffer
        screenState.stageImageBytesForTesting(
          bytes: Uint8List(0),
          fileName: 'empty_file.png',
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('photoErrorBanner')), findsOneWidget);
        expect(find.text(AppStrings.photoErrorCorrupt), findsOneWidget);

        // 2. Oversized buffer (> 5 MB)
        screenState.stageImageBytesForTesting(
          bytes: Uint8List(5 * 1024 * 1024 + 1024),
          fileName: 'oversized_photo.jpg',
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('photoErrorBanner')), findsOneWidget);
        expect(find.text(AppStrings.photoErrorTooLarge), findsOneWidget);

        // 3. Invalid magic bytes (e.g., text / corrupted payload)
        screenState.stageImageBytesForTesting(
          bytes: Uint8List.fromList([0x12, 0x34, 0x56, 0x78, 0x9A]),
          fileName: 'not_an_image.bin',
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('photoErrorBanner')), findsOneWidget);
        expect(find.text(AppStrings.photoErrorUnsupported), findsOneWidget);
      },
    );

    testWidgets(
      'Photo staging: selecting candidate renders metadata chips, circular crop guide, and zoom slider',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'stager@digitaltrust.ai',
          userName: 'Staging Inspector',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ProfilePhotoScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Initially no staging card
        expect(find.byKey(const Key('photoStagingCard')), findsNothing);

        // Tap sample PNG button
        final pngBtn = find.byKey(const Key('selectPngSampleButton'));
        await tester.ensureVisible(pngBtn);
        await tester.tap(pngBtn);
        await tester.pumpAndSettle();

        // Staging card and preview elements rendered
        expect(find.byKey(const Key('photoStagingCard')), findsOneWidget);
        expect(find.byKey(const Key('stagedFileNameChip')), findsOneWidget);
        expect(find.byKey(const Key('stagedFormatChip')), findsOneWidget);
        expect(find.byKey(const Key('stagedSizeChip')), findsOneWidget);
        expect(find.byKey(const Key('stagedPhotoPreviewImage')), findsOneWidget);
        expect(find.byKey(const Key('cropOverlayGuide')), findsOneWidget);
        expect(find.byKey(const Key('cropZoomSlider')), findsOneWidget);

        // Cancel selection
        final cancelBtn = find.byKey(const Key('cancelSelectionButton'));
        await tester.ensureVisible(cancelBtn);
        await tester.tap(cancelBtn);
        await tester.pumpAndSettle();

        // Staging dismissed, back to dropzone
        expect(find.byKey(const Key('photoStagingCard')), findsNothing);
        expect(find.byKey(const Key('photoDropZonePlaceholder')), findsOneWidget);
      },
    );

    testWidgets(
      'Confirming upload: uploads photo to private storage, updates AuthService, and shows success snackbar',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'uploader@digitaltrust.ai',
          userName: 'Uploader User',
          userId: 'usr_up_100',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ProfilePhotoScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Stage photo
        final sampleBtn = find.byKey(const Key('selectJpegSampleButton'));
        await tester.ensureVisible(sampleBtn);
        await tester.tap(sampleBtn);
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('photoStagingCard')), findsOneWidget);

        // Confirm upload
        final confirmBtn = find.byKey(const Key('confirmUploadPhotoButton'));
        await tester.ensureVisible(confirmBtn);
        await tester.tap(confirmBtn);
        await tester.pumpAndSettle();

        // Success snackbar and AuthService state update
        expect(find.byKey(const Key('photoSuccessSnackBar')), findsOneWidget);
        expect(find.text(AppStrings.photoSuccessUpload), findsOneWidget);
        expect(AuthService.instance.hasProfilePhoto, isTrue);
        expect(AuthService.instance.profilePhotoPath, contains('avatar'));
        expect(find.byKey(const Key('currentPhotoMemoryImage')), findsOneWidget);
      },
    );

    testWidgets(
      'Upload failure: displays error banner when storage rejects upload',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'error.tester@digitaltrust.ai',
          userName: 'Error Tester',
        );

        // Inject simulated backend upload error
        AuthService.instance.setPhotoDelegatesForTesting(
          uploadDelegate: ({required fileBytes, required fileName}) async =>
              ProfilePhotoUploadResult.failure(
            'Row Level Security policy rejected upload: Unauthorized user identity.',
          ),
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ProfilePhotoScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Stage photo
        final sampleBtn = find.byKey(const Key('selectWebpSampleButton'));
        await tester.ensureVisible(sampleBtn);
        await tester.tap(sampleBtn);
        await tester.pumpAndSettle();

        // Confirm upload
        final confirmBtn = find.byKey(const Key('confirmUploadPhotoButton'));
        await tester.ensureVisible(confirmBtn);
        await tester.tap(confirmBtn);
        await tester.pumpAndSettle();

        // Error banner is rendered
        expect(find.byKey(const Key('photoErrorBanner')), findsOneWidget);
        expect(
          find.text('Row Level Security policy rejected upload: Unauthorized user identity.'),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Remove photo: confirmation dialog cancels safely, and confirming reverts to neutral avatar',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'remover@digitaltrust.ai',
          userName: 'Remover User',
        );

        final sampleBytes = Uint8List.fromList([
          0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
          0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
          0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00,
          0x0A, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
          0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49,
          0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
        ]);
        AuthService.instance.setProfilePhotoForTesting(
          filePath: 'remover/avatar.png',
          bytes: sampleBytes,
          signedUrl: 'https://storage.supabase.co/profile-photos/signed',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const ProfilePhotoScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final removeBtn = find.byKey(const Key('removePhotoButton'));
        await tester.ensureVisible(removeBtn);
        await tester.tap(removeBtn);
        await tester.pumpAndSettle();

        // Dialog opened
        expect(find.byKey(const Key('removePhotoConfirmDialog')), findsOneWidget);
        expect(find.text(AppStrings.photoRemovingTitle), findsOneWidget);

        // Cancel
        await tester.tap(find.byKey(const Key('cancelRemovePhotoButton')));
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('removePhotoConfirmDialog')), findsNothing);
        expect(AuthService.instance.hasProfilePhoto, isTrue);

        // Tap remove again and confirm
        await tester.tap(removeBtn);
        await tester.pumpAndSettle();
        await tester.tap(find.byKey(const Key('confirmRemovePhotoButton')));
        await tester.pumpAndSettle();

        // Verified reverted state
        expect(AuthService.instance.hasProfilePhoto, isFalse);
        expect(find.byKey(const Key('photoRemovedSnackBar')), findsOneWidget);
        expect(find.text(AppStrings.photoSuccessRemove), findsOneWidget);
        expect(find.byKey(const Key('neutralPhotoAvatarPlaceholder')), findsOneWidget);
      },
    );

    testWidgets(
      'Unauthenticated state: renders security barrier card and redirects to sign in',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const ProfilePhotoScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('unauthenticatedCard')), findsOneWidget);
        expect(find.text(AppStrings.profileUnauthenticatedTitle), findsOneWidget);
        expect(find.byKey(const Key('profilePhotoSignInButton')), findsOneWidget);

        await tester.tap(find.byKey(const Key('profilePhotoSignInButton')));
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'UserProfileOverviewScreen integration: tapping avatar navigates to ProfilePhotoScreen',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'overview@digitaltrust.ai',
          userName: 'Overview User',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserProfileOverviewScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final avatarButton = find.byKey(const Key('profileAvatarButton'));
        expect(avatarButton, findsOneWidget);
        await tester.tap(avatarButton);
        await tester.pumpAndSettle();

        expect(find.byType(ProfilePhotoScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Responsive rendering across mobile to desktop sizes without layout overflow',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'responsive@digitaltrust.ai',
          userName: 'Responsive Photo User',
        );

        final screenSizes = [
          const Size(320, 568),  // Small mobile
          const Size(390, 844),  // Standard mobile
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const ProfilePhotoScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.byKey(const Key('profilePhotoHeading')), findsOneWidget);
          expect(find.byKey(const Key('currentPhotoCard')), findsOneWidget);
          expect(find.byKey(const Key('photoGuidelinesCard')), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );
  });

  group('Screen 027 — Verification Status & Progress Screen Tests', () {
    setUp(() {
      AuthService.instance.resetToDefault();
    });

    tearDown(() {
      AuthService.instance.resetToDefault();
    });

    testWidgets(
      'Renders heading, subtitle, summary card, posture banner, and requests when authenticated',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'status_user@digitaltrust.ai',
          userName: 'Status User',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const VerificationStatusScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Header & typography
        expect(find.text(AppStrings.verificationStatusHeading), findsOneWidget);
        expect(find.text(AppStrings.verificationStatusSubtitle), findsOneWidget);

        // Summary Card & Elements
        expect(find.byKey(const Key('verificationSummaryCard')), findsOneWidget);
        expect(find.byKey(const Key('verificationPostureBanner')), findsOneWidget);
        expect(
          find.byKey(const Key('verificationDistinctionNoticeBanner')),
          findsOneWidget,
        );

        // Breakdown Chips
        expect(find.byKey(const Key('summaryChipTotal')), findsOneWidget);
        expect(find.byKey(const Key('summaryChipActionRequired')), findsOneWidget);
        expect(find.byKey(const Key('summaryChipVerified')), findsOneWidget);

        // Requests list cards
        expect(
          find.byKey(const Key('verificationRequestCard_vr_req_9011')),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('verificationRequestCard_vr_req_8410')),
          findsOneWidget,
        );

        // Reviewer feedback and action required alerts rendered
        expect(
          find.byKey(const Key('reviewerFeedback_vr_req_9011')),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('actionRequiredBanner_vr_req_9011')),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('verificationResubmit_vr_req_9011')),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Filter tabs cleanly filter verification requests by status',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'filter_user@digitaltrust.ai',
          userName: 'Filter User',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const VerificationStatusScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Initially both requests are rendered
        expect(find.byKey(const Key('verificationRequestCard_vr_req_9011')), findsOneWidget);
        expect(find.byKey(const Key('verificationRequestCard_vr_req_8410')), findsOneWidget);

        // Tap "Action Required" filter
        final actionFilter = find.byKey(
          Key('filterChip_${AppStrings.verificationFilterActionRequired}'),
        );
        await tester.ensureVisible(actionFilter);
        await tester.tap(actionFilter);
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('verificationRequestCard_vr_req_9011')), findsOneWidget);
        expect(find.byKey(const Key('verificationRequestCard_vr_req_8410')), findsNothing);

        // Tap "Verified" filter
        final verifiedFilter = find.byKey(
          Key('filterChip_${AppStrings.verificationFilterVerified}'),
        );
        await tester.ensureVisible(verifiedFilter);
        await tester.tap(verifiedFilter);
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('verificationRequestCard_vr_req_9011')), findsNothing);
        expect(find.byKey(const Key('verificationRequestCard_vr_req_8410')), findsOneWidget);

        // Tap "Rejected" filter -> shows filter empty state
        final rejectedFilter = find.byKey(
          Key('filterChip_${AppStrings.verificationFilterRejected}'),
        );
        await tester.ensureVisible(rejectedFilter);
        await tester.tap(rejectedFilter);
        await tester.pumpAndSettle();

        expect(find.text('No requests match "${AppStrings.verificationFilterRejected}"'), findsOneWidget);

        // Tap "Reset Filter"
        final resetBtn = find.text('Reset Filter');
        await tester.ensureVisible(resetBtn);
        await tester.tap(resetBtn);
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('verificationRequestCard_vr_req_9011')), findsOneWidget);
        expect(find.byKey(const Key('verificationRequestCard_vr_req_8410')), findsOneWidget);
      },
    );

    testWidgets(
      'View Details opens VerificationDetailsDialog with masked document numbers and audit timeline',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'details_user@digitaltrust.ai',
          userName: 'Details User',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const VerificationStatusScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Tap View Details on vr_req_9011
        final viewDetailsBtn = find.byKey(
          const Key('verificationViewDetails_vr_req_9011'),
        );
        expect(viewDetailsBtn, findsOneWidget);
        await tester.ensureVisible(viewDetailsBtn);
        await tester.tap(viewDetailsBtn);
        await tester.pumpAndSettle();

        // Dialog opened
        expect(find.byKey(const Key('verificationDetailsDialog')), findsOneWidget);
        expect(find.text(AppStrings.verificationDetailsModalTitle), findsOneWidget);
        expect(
          find.text(AppStrings.verificationDetailsDocumentsSection),
          findsOneWidget,
        );

        // Privacy safeguard: National ID / Aadhaar is masked, not exposed in plaintext
        expect(find.text('Credential ID: •••• •••• 4289'), findsOneWidget);

        // Audit timeline rendered
        expect(
          find.text(AppStrings.verificationDetailsTimelineSection),
          findsOneWidget,
        );
        expect(find.text('Request Created'), findsOneWidget);
        expect(find.text('Credentials Submitted'), findsOneWidget);
        expect(find.text('Compliance Review'), findsOneWidget);

        // Close dialog
        await tester.tap(find.byKey(const Key('verificationDetailsCloseButton')));
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('verificationDetailsDialog')), findsNothing);
      },
    );

    testWidgets(
      'Resubmit Documents triggers retry action and displays confirmation toast',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'retry_user@digitaltrust.ai',
          userName: 'Retry User',
        );

        String? retriedId;
        AuthService.instance.setRetryVerificationDelegate(
          ({required String requestId}) async {
            retriedId = requestId;
            return true;
          },
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const VerificationStatusScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        final resubmitBtn = find.byKey(
          const Key('verificationResubmit_vr_req_9011'),
        );
        expect(resubmitBtn, findsOneWidget);
        await tester.ensureVisible(resubmitBtn);
        await tester.tap(resubmitBtn);
        await tester.pumpAndSettle();

        expect(retriedId, 'vr_req_9011');
        expect(
          find.byKey(const Key('verificationResubmitSuccessSnackBar')),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.verificationResubmitSuccess),
          findsOneWidget,
        );
      },
    );

    testWidgets(
      'Empty state: displays honest empty state when no verification requests exist',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'empty_user@digitaltrust.ai',
          userName: 'Empty User',
        );
        AuthService.instance.setVerificationRequestsDelegate(() async => []);

        await tester.pumpWidget(
          MaterialApp(
            home: const VerificationStatusScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('verificationEmptyState')), findsOneWidget);
        expect(find.text(AppStrings.verificationEmptyTitle), findsOneWidget);
        expect(find.text(AppStrings.verificationEmptyDesc), findsOneWidget);
      },
    );

    testWidgets(
      'Error state: displays load error banner and retries cleanly',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'error_user@digitaltrust.ai',
          userName: 'Error User',
        );

        bool shouldFail = true;
        AuthService.instance.setVerificationRequestsDelegate(() async {
          if (shouldFail) {
            throw Exception('Simulated network failure');
          }
          return [];
        });

        await tester.pumpWidget(
          MaterialApp(
            home: const VerificationStatusScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('verificationLoadErrorBanner')), findsOneWidget);
        expect(find.text(AppStrings.verificationLoadErrorTitle), findsOneWidget);

        // Tap Retry Query
        shouldFail = false;
        final retryBtn = find.byKey(const Key('verificationRetryQueryButton'));
        expect(retryBtn, findsOneWidget);
        await tester.tap(retryBtn);
        await tester.pumpAndSettle();

        expect(find.byKey(const Key('verificationLoadErrorBanner')), findsNothing);
        expect(find.byKey(const Key('verificationEmptyState')), findsOneWidget);
      },
    );

    testWidgets(
      'Unauthenticated state: displays security barrier card and redirects to sign in',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: const VerificationStatusScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(
          find.byKey(const Key('verificationUnauthenticatedBarrier')),
          findsOneWidget,
        );
        expect(
          find.text(AppStrings.verificationUnauthenticatedTitle),
          findsOneWidget,
        );
        expect(
          find.byKey(const Key('verificationSignInButton')),
          findsOneWidget,
        );

        await tester.tap(find.byKey(const Key('verificationSignInButton')));
        await tester.pumpAndSettle();

        expect(find.byType(LoginScreen), findsOneWidget);
      },
    );

    testWidgets(
      'Responsive rendering across mobile to desktop sizes without layout overflow',
      (WidgetTester tester) async {
        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'responsive@digitaltrust.ai',
          userName: 'Responsive User',
        );

        final screenSizes = [
          const Size(320, 568),  // Small mobile
          const Size(390, 844),  // Standard mobile
          const Size(768, 1024), // Tablet portrait
          const Size(1024, 768), // Tablet landscape
          const Size(1440, 900), // Desktop
        ];

        for (final size in screenSizes) {
          tester.view.physicalSize = size;
          tester.view.devicePixelRatio = 1.0;

          await tester.pumpWidget(
            MaterialApp(
              key: UniqueKey(),
              home: const VerificationStatusScreen(),
              onGenerateRoute: AppRoutes.onGenerateRoute,
            ),
          );
          await tester.pumpAndSettle();

          expect(find.text(AppStrings.verificationStatusHeading), findsOneWidget);
          expect(find.byKey(const Key('verificationSummaryCard')), findsOneWidget);
        }

        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
      },
    );

    testWidgets(
      'Dashboard & Sidebar routing integration: routes to VerificationStatusScreen',
      (WidgetTester tester) async {
        tester.view.physicalSize = const Size(1440, 900);
        tester.view.devicePixelRatio = 1.0;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        AuthService.instance.setAuthenticatedSessionForTesting(
          email: 'nav_user@digitaltrust.ai',
          userName: 'Nav User',
        );

        await tester.pumpWidget(
          MaterialApp(
            home: const UserDashboardScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        // Desktop layout sidebar navigation item
        final sidebarNav = find.byKey(const Key('sidebarNavVerification'));
        expect(sidebarNav, findsOneWidget);
        await tester.tap(sidebarNav);
        await tester.pumpAndSettle();

        expect(find.byType(VerificationStatusScreen), findsOneWidget);
      },
    );
  });
}



