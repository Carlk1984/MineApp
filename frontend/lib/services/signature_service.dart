import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:signature/signature.dart';
import 'package:flutter/material.dart';

class SignatureService {
  static SignatureController createController({
    Color penColor = Colors.black,
    double penStrokeWidth = 2.0,
    Color backgroundColor = Colors.white,
  }) {
    return SignatureController(
      penStrokeWidth: penStrokeWidth,
      penColor: penColor,
      exportBackgroundColor: backgroundColor,
    );
  }

  static Future<Uint8List?> exportSignature(SignatureController controller) async {
    if (controller.isEmpty) return null;
    
    try {
      final signature = await controller.toPngBytes();
      return signature;
    } catch (e) {
      debugPrint('Error exporting signature: $e');
      return null;
    }
  }

  static Widget buildSignaturePad({
    required SignatureController controller,
    double height = 200,
    String? label,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (label != null) ...[
          Text(
            label,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
        ],
        Container(
          height: height,
          decoration: BoxDecoration(
            border: Border.all(color: Colors.grey),
            borderRadius: BorderRadius.circular(8),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Signature(
              controller: controller,
              backgroundColor: Colors.white,
            ),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            TextButton.icon(
              onPressed: () => controller.clear(),
              icon: const Icon(Icons.clear),
              label: const Text('Clear'),
            ),
          ],
        ),
      ],
    );
  }

  static Future<bool> showSignatureDialog({
    required BuildContext context,
    required Function(Uint8List) onSignatureSaved,
    String title = 'Add Signature',
    String? description,
  }) async {
    final controller = createController();
    
    final result = await showDialog<bool>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text(title),
          content: SizedBox(
            width: double.maxFinite,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (description != null) ...[
                  Text(description),
                  const SizedBox(height: 16),
                ],
                buildSignaturePad(controller: controller),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final signature = await exportSignature(controller);
                if (signature != null) {
                  onSignatureSaved(signature);
                  if (context.mounted) {
                    Navigator.of(context).pop(true);
                  }
                } else {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Please provide a signature'),
                        backgroundColor: Colors.orange,
                      ),
                    );
                  }
                }
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
    
    controller.dispose();
    return result ?? false;
  }
}
