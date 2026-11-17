import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ai_trust_platform/core/routing/app_routes.dart';
import 'package:ai_trust_platform/screens/documents/digital_documents_screen.dart';

void main() {
  group('Digital Documents Screen Tests', () {
    testWidgets('Renders DigitalDocumentsScreen with header, banner, and document cards', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: const DigitalDocumentsScreen(),
          onGenerateRoute: AppRoutes.onGenerateRoute,
        ),
      );
      await tester.pumpAndSettle();

      // Top Header
      expect(find.text('Digital Document Vault'), findsOneWidget);
      expect(find.textContaining('Upload'), findsWidgets);

      // Vault Banner
      expect(find.text('AI Identity & Document Trust Vault'), findsOneWidget);
      expect(find.text('AES-256 ENCRYPTED'), findsOneWidget);

      // Default Seeded Document Cards
      expect(find.text('State Driving Licence'), findsOneWidget);
      expect(find.text('Permanent Account Number (PAN)'), findsOneWidget);
      expect(find.text('Aadhaar National Identity'), findsOneWidget);

      // View Details Buttons
      expect(find.text('View Details'), findsWidgets);
    });

    testWidgets('Search input filters document list correctly', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: const DigitalDocumentsScreen(),
          onGenerateRoute: AppRoutes.onGenerateRoute,
        ),
      );
      await tester.pumpAndSettle();

      // Enter search term
      await tester.enterText(find.byType(TextField), 'PAN');
      await tester.pumpAndSettle();

      expect(find.text('Permanent Account Number (PAN)'), findsOneWidget);
      expect(find.text('State Driving Licence'), findsNothing);
    });

    testWidgets('Renders without overflow on varied screen sizes', (
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
            home: const DigitalDocumentsScreen(),
            onGenerateRoute: AppRoutes.onGenerateRoute,
          ),
        );
        await tester.pumpAndSettle();

        expect(find.byType(DigitalDocumentsScreen), findsOneWidget);
      }

      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
    });
  });
}
