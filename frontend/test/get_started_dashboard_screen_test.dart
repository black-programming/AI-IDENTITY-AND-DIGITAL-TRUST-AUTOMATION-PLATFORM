import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_trust_platform/core/routing/app_routes.dart';
import 'package:ai_trust_platform/screens/dashboard/get_started_dashboard_screen.dart';
import 'package:ai_trust_platform/screens/dashboard/widgets/mvp_verification_hub_card.dart';

void main() {
  group('Get Started Dashboard Screen Tests', () {
    testWidgets('Renders all elements: AppBar, Verification Hub, and Sign Up banner', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: const GetStartedDashboardScreen(),
          onGenerateRoute: AppRoutes.onGenerateRoute,
        ),
      );
      await tester.pumpAndSettle();

      // Top AppBar & Header
      expect(find.byKey(const Key('getStartedDashboardScaffold')), findsOneWidget);
      expect(find.byKey(const Key('getStartedDashboardBackButton')), findsOneWidget);
      expect(find.text('Get Started — Verification Hub'), findsOneWidget);
      expect(find.byKey(const Key('getStartedSignInButton')), findsOneWidget);

      // Section Title & Explainer
      expect(find.text('Instant Document Verification Dashboard'), findsOneWidget);

      // Centerpiece: MVP Verification Hub Card with document options
      expect(find.byType(MvpVerificationHubCard), findsOneWidget);
      expect(find.text('Driving Licence'), findsOneWidget);
      expect(find.text('PAN Card'), findsOneWidget);
      expect(find.text('Aadhaar Card'), findsOneWidget);

      // Conversion Card & Sign Up Button
      expect(find.text('Need a permanent verified profile?'), findsOneWidget);
      expect(find.byKey(const Key('getStartedCreateAccountButton')), findsOneWidget);
    });

    testWidgets('Tapping Sign Up Now navigates to Create Account screen', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: const GetStartedDashboardScreen(),
          onGenerateRoute: AppRoutes.onGenerateRoute,
        ),
      );
      await tester.pumpAndSettle();

      final signUpFinder = find.byKey(const Key('getStartedCreateAccountButton'));
      await tester.ensureVisible(signUpFinder);
      await tester.tap(signUpFinder);
      await tester.pumpAndSettle();

      // Verified arrival on Create Account Screen
      expect(find.text('Create Account'), findsWidgets);
    });

    testWidgets('Renders GetStartedDashboardScreen without overflow on varied screen sizes', (
      WidgetTester tester,
    ) async {
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
            home: const GetStartedDashboardScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byType(GetStartedDashboardScreen), findsOneWidget);
        expect(find.byType(MvpVerificationHubCard), findsOneWidget);
      }

      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
    });
  });
}
