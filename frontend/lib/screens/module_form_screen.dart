import 'dart:io';
import 'dart:typed_data';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../services/hive_service.dart';
import '../services/camera_service.dart';
import '../services/location_service.dart';
import '../services/signature_service.dart';
import '../models/record.dart';

class ModuleFormScreen extends StatefulWidget {
  final String moduleName;
  
  const ModuleFormScreen({super.key, required this.moduleName});

  @override
  State<ModuleFormScreen> createState() => _ModuleFormScreenState();
}

class _ModuleFormScreenState extends State<ModuleFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final Map<String, dynamic> _formData = {};
  final Map<String, TextEditingController> _controllers = {};
  final Map<String, File> _photos = {};
  final Map<String, Uint8List> _signatures = {};
  LocationData? _currentLocation;
  bool _isSubmitting = false;
  bool _isOffline = false;
  bool _locationEnabled = true;

  @override
  void initState() {
    super.initState();
    _checkConnectivity();
    _initializeControllers();
  }

  @override
  void dispose() {
    for (var controller in _controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  void _initializeControllers() {
    final fields = _getFormFields();
    for (var field in fields) {
      if (field['type'] != 'photo' && field['type'] != 'signature' && field['type'] != 'location') {
        _controllers[field['key']] = TextEditingController();
      }
    }
    _getCurrentLocation();
  }

  void _getCurrentLocation() async {
    if (_locationEnabled) {
      final location = await LocationService.getCurrentLocation();
      if (location != null) {
        setState(() {
          _currentLocation = location;
        });
      }
    }
  }

  void _checkConnectivity() async {
    final connectivityResult = await Connectivity().checkConnectivity();
    setState(() {
      _isOffline = connectivityResult == ConnectivityResult.none;
    });
  }

  List<Map<String, dynamic>> _getFormFields() {
    switch (widget.moduleName) {
      case 'Milling':
        return [
          {'key': 'tonnage_processed', 'label': 'Tonnage Processed (tons)', 'type': 'number', 'required': true},
          {'key': 'mill_availability', 'label': 'Mill Availability (%)', 'type': 'number', 'required': true},
          {'key': 'throughput_rate', 'label': 'Throughput Rate (t/h)', 'type': 'number', 'required': true},
          {'key': 'power_consumption', 'label': 'Power Consumption (kWh)', 'type': 'number', 'required': true},
          {'key': 'maintenance_hours', 'label': 'Maintenance Hours', 'type': 'number', 'required': false},
          {'key': 'operator_notes', 'label': 'Operator Notes', 'type': 'text', 'required': false},
          {'key': 'equipment_photo', 'label': 'Equipment Photo', 'type': 'photo', 'required': false},
        ];
      case 'Extraction':
        return [
          {'key': 'ore_extracted', 'label': 'Ore Extracted (tons)', 'type': 'number', 'required': true},
          {'key': 'waste_removed', 'label': 'Waste Removed (tons)', 'type': 'number', 'required': true},
          {'key': 'equipment_hours', 'label': 'Equipment Operating Hours', 'type': 'number', 'required': true},
          {'key': 'fuel_consumption', 'label': 'Fuel Consumption (L)', 'type': 'number', 'required': true},
          {'key': 'safety_incidents', 'label': 'Safety Incidents', 'type': 'number', 'required': true},
          {'key': 'weather_conditions', 'label': 'Weather Conditions', 'type': 'select', 'options': ['Clear', 'Rainy', 'Windy', 'Stormy'], 'required': true},
          {'key': 'incident_photo', 'label': 'Incident Documentation Photo', 'type': 'photo', 'required': false},
        ];
      case 'Blasting':
        return [
          {'key': 'blast_holes', 'label': 'Number of Blast Holes', 'type': 'number', 'required': true},
          {'key': 'explosive_used', 'label': 'Explosive Used (kg)', 'type': 'number', 'required': true},
          {'key': 'rock_fragmentation', 'label': 'Rock Fragmentation Quality', 'type': 'select', 'options': ['Excellent', 'Good', 'Fair', 'Poor'], 'required': true},
          {'key': 'blast_efficiency', 'label': 'Blast Efficiency (%)', 'type': 'number', 'required': true},
          {'key': 'safety_clearance', 'label': 'Safety Clearance Distance (m)', 'type': 'number', 'required': true},
          {'key': 'environmental_impact', 'label': 'Environmental Impact Assessment', 'type': 'text', 'required': false},
        ];
      case 'Ore Movement':
        return [
          {'key': 'trucks_operated', 'label': 'Number of Trucks Operated', 'type': 'number', 'required': true},
          {'key': 'total_distance', 'label': 'Total Distance Traveled (km)', 'type': 'number', 'required': true},
          {'key': 'fuel_efficiency', 'label': 'Fuel Efficiency (L/100km)', 'type': 'number', 'required': true},
          {'key': 'load_cycles', 'label': 'Number of Load Cycles', 'type': 'number', 'required': true},
          {'key': 'downtime_hours', 'label': 'Equipment Downtime (hours)', 'type': 'number', 'required': false},
          {'key': 'route_conditions', 'label': 'Route Conditions', 'type': 'select', 'options': ['Excellent', 'Good', 'Fair', 'Poor'], 'required': true},
        ];
      case 'Gold Refining':
        return [
          {'key': 'gold_input', 'label': 'Gold Input (oz)', 'type': 'number', 'required': true},
          {'key': 'gold_output', 'label': 'Gold Output (oz)', 'type': 'number', 'required': true},
          {'key': 'purity_level', 'label': 'Purity Level (%)', 'type': 'number', 'required': true},
          {'key': 'processing_time', 'label': 'Processing Time (hours)', 'type': 'number', 'required': true},
          {'key': 'chemical_usage', 'label': 'Chemical Usage (L)', 'type': 'number', 'required': true},
          {'key': 'quality_control', 'label': 'Quality Control Notes', 'type': 'text', 'required': false},
          {'key': 'quality_photo', 'label': 'Quality Control Photo', 'type': 'photo', 'required': false},
        ];
      case 'Materials & Assets':
        return [
          {'key': 'inventory_count', 'label': 'Inventory Items Counted', 'type': 'number', 'required': true},
          {'key': 'new_acquisitions', 'label': 'New Equipment/Materials', 'type': 'text', 'required': false},
          {'key': 'maintenance_completed', 'label': 'Maintenance Tasks Completed', 'type': 'number', 'required': true},
          {'key': 'asset_condition', 'label': 'Overall Asset Condition', 'type': 'select', 'options': ['Excellent', 'Good', 'Fair', 'Poor'], 'required': true},
          {'key': 'replacement_needed', 'label': 'Equipment Needing Replacement', 'type': 'text', 'required': false},
          {'key': 'cost_tracking', 'label': 'Cost Tracking Notes', 'type': 'text', 'required': false},
          {'key': 'asset_photo', 'label': 'Asset Condition Photo', 'type': 'photo', 'required': false},
        ];
      default:
        return [];
    }
  }

  List<Map<String, dynamic>> _getCommonFields() {
    return [
      {'key': 'operator_signature', 'label': 'Operator Signature', 'type': 'signature', 'required': true},
    ];
  }

  Widget _buildFormField(Map<String, dynamic> field) {
    switch (field['type']) {
      case 'number':
        return TextFormField(
          controller: _controllers[field['key']],
          decoration: InputDecoration(
            labelText: field['label'],
            border: const OutlineInputBorder(),
          ),
          keyboardType: TextInputType.number,
          validator: field['required'] ? (value) {
            if (value == null || value.isEmpty) {
              return 'This field is required';
            }
            if (double.tryParse(value) == null) {
              return 'Please enter a valid number';
            }
            return null;
          } : null,
        );
      case 'text':
        return TextFormField(
          controller: _controllers[field['key']],
          decoration: InputDecoration(
            labelText: field['label'],
            border: const OutlineInputBorder(),
          ),
          maxLines: field['key'].contains('notes') ? 3 : 1,
          validator: field['required'] ? (value) {
            if (value == null || value.isEmpty) {
              return 'This field is required';
            }
            return null;
          } : null,
        );
      case 'select':
        return DropdownButtonFormField<String>(
          decoration: InputDecoration(
            labelText: field['label'],
            border: const OutlineInputBorder(),
          ),
          items: (field['options'] as List<String>).map((option) {
            return DropdownMenuItem(value: option, child: Text(option));
          }).toList(),
          validator: field['required'] ? (value) {
            if (value == null || value.isEmpty) {
              return 'This field is required';
            }
            return null;
          } : null,
          onChanged: (value) {
            if (value != null) {
              _formData[field['key']] = value;
            }
          },
        );
      case 'photo':
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              field['label'],
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 8),
            if (_photos[field['key']] != null) ...[
              Container(
                height: 200,
                width: double.infinity,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.file(
                    _photos[field['key']]!,
                    fit: BoxFit.cover,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  ElevatedButton.icon(
                    onPressed: () => _capturePhoto(field['key']),
                    icon: const Icon(Icons.camera_alt),
                    label: const Text('Retake'),
                  ),
                  const SizedBox(width: 8),
                  TextButton.icon(
                    onPressed: () => _removePhoto(field['key']),
                    icon: const Icon(Icons.delete),
                    label: const Text('Remove'),
                  ),
                ],
              ),
            ] else ...[
              ElevatedButton.icon(
                onPressed: () => _capturePhoto(field['key']),
                icon: const Icon(Icons.camera_alt),
                label: Text('Add ${field['label']}'),
              ),
            ],
          ],
        );
      case 'signature':
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              field['label'],
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 8),
            if (_signatures[field['key']] != null) ...[
              Container(
                height: 150,
                width: double.infinity,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.memory(
                    _signatures[field['key']]!,
                    fit: BoxFit.contain,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  ElevatedButton.icon(
                    onPressed: () => _captureSignature(field['key'], field['label']),
                    icon: const Icon(Icons.edit),
                    label: const Text('Edit'),
                  ),
                  const SizedBox(width: 8),
                  TextButton.icon(
                    onPressed: () => _removeSignature(field['key']),
                    icon: const Icon(Icons.delete),
                    label: const Text('Remove'),
                  ),
                ],
              ),
            ] else ...[
              ElevatedButton.icon(
                onPressed: () => _captureSignature(field['key'], field['label']),
                icon: const Icon(Icons.edit),
                label: Text('Add ${field['label']}'),
              ),
              if (field['required'] == true)
                const Text(
                  'Required',
                  style: TextStyle(color: Colors.red, fontSize: 12),
                ),
            ],
          ],
        );
      default:
        return const SizedBox.shrink();
    }
  }

  Future<void> _capturePhoto(String fieldKey) async {
    final photo = await CameraService.showImageSourceDialog(context);
    if (photo != null) {
      setState(() {
        _photos[fieldKey] = photo;
      });
    }
  }

  void _removePhoto(String fieldKey) {
    setState(() {
      _photos.remove(fieldKey);
    });
  }

  Future<void> _captureSignature(String fieldKey, String label) async {
    await SignatureService.showSignatureDialog(
      context: context,
      title: 'Add $label',
      onSignatureSaved: (signature) {
        setState(() {
          _signatures[fieldKey] = signature;
        });
      },
    );
  }

  void _removeSignature(String fieldKey) {
    setState(() {
      _signatures.remove(fieldKey);
    });
  }

  void _collectFormData() {
    final fields = _getFormFields();
    final commonFields = _getCommonFields();
    final allFields = [...fields, ...commonFields];
    
    for (var field in allFields) {
      if (field['type'] == 'photo') {
        final photo = _photos[field['key']];
        if (photo != null) {
          final bytes = photo.readAsBytesSync();
          _formData[field['key']] = base64Encode(bytes);
        }
      } else if (field['type'] == 'signature') {
        final signature = _signatures[field['key']];
        if (signature != null) {
          _formData[field['key']] = base64Encode(signature);
        }
      } else {
        final controller = _controllers[field['key']];
        if (controller != null && controller.text.isNotEmpty) {
          if (field['type'] == 'number') {
            _formData[field['key']] = double.tryParse(controller.text) ?? 0;
          } else {
            _formData[field['key']] = controller.text;
          }
        }
      }
    }
  }

  Future<void> _submitForm() async {
    if (!_formKey.currentState!.validate()) return;

    final commonFields = _getCommonFields();
    for (var field in commonFields) {
      if (field['required'] == true) {
        if (field['type'] == 'signature' && _signatures[field['key']] == null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('${field['label']} is required'),
              backgroundColor: Colors.red,
            ),
          );
          return;
        }
      }
    }

    _collectFormData();
    
    setState(() {
      _isSubmitting = true;
    });

    try {
      final authService = Provider.of<AuthService>(context, listen: false);
      final apiService = Provider.of<ApiService>(context, listen: false);
      
      _formData['manager_on_duty'] = 'Manager Name';
      
      final photos = <String>[];
      for (var entry in _photos.entries) {
        final bytes = entry.value.readAsBytesSync();
        photos.add(base64Encode(bytes));
      }
      
      String? signatureData;
      if (_signatures.isNotEmpty) {
        final signature = _signatures.values.first;
        signatureData = base64Encode(signature);
      }
      
      final record = Record(
        id: '',
        module: widget.moduleName,
        data: _formData,
        managerOnDuty: _formData['manager_on_duty'],
        submittedBy: authService.currentUser?.id ?? '',
        approvalStatus: 'pending',
        timestamp: DateTime.now(),
        locationData: _currentLocation,
        photos: photos.isNotEmpty ? photos : null,
        signature: signatureData,
      );

      if (_isOffline) {
        final hiveService = Provider.of<HiveService>(context, listen: false);
        await hiveService.saveOfflineRecord(record);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Form saved offline. Will sync when connection is restored.'),
              backgroundColor: Colors.orange,
            ),
          );
          Navigator.of(context).pop();
        }
      } else {
        final token = authService.getAuthHeader();
        if (token != null) {
          final recordData = {
            'module': widget.moduleName,
            'data': _formData,
            'manager_on_duty': _formData['manager_on_duty'],
          };
          await apiService.createRecord(token.replaceFirst('Bearer ', ''), recordData);
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Form submitted successfully!'),
                backgroundColor: Colors.green,
              ),
            );
            Navigator.of(context).pop();
          }
        } else {
          throw Exception('Authentication token not available');
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final formFields = _getFormFields();
    final commonFields = _getCommonFields();
    
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.moduleName} Entry'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          if (_isOffline)
            const Padding(
              padding: EdgeInsets.all(8.0),
              child: Chip(
                label: Text('OFFLINE'),
                backgroundColor: Colors.orange,
              ),
            ),
          IconButton(
            icon: Icon(_locationEnabled ? Icons.location_on : Icons.location_off),
            onPressed: () {
              setState(() {
                _locationEnabled = !_locationEnabled;
                if (_locationEnabled) {
                  _getCurrentLocation();
                } else {
                  _currentLocation = null;
                }
              });
            },
            tooltip: _locationEnabled ? 'Disable Location' : 'Enable Location',
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Module: ${widget.moduleName}',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Date: ${DateTime.now().toString().split(' ')[0]}',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _isOffline ? 'Status: Offline Mode' : 'Status: Online',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: _isOffline ? Colors.orange : Colors.green,
                      ),
                    ),
                    if (_currentLocation != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        'Location: ${LocationService.formatLocation(_currentLocation!)}',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.blue,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            ...formFields.map((field) => Padding(
              padding: const EdgeInsets.only(bottom: 16.0),
              child: _buildFormField(field),
            )),
            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 16),
            Text(
              'Validation',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            ...commonFields.map((field) => Padding(
              padding: const EdgeInsets.only(bottom: 16.0),
              child: _buildFormField(field),
            )),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _isSubmitting ? null : _submitForm,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: _isSubmitting
                ? const CircularProgressIndicator()
                : Text(_isOffline ? 'Save Offline' : 'Submit Form'),
            ),
          ],
        ),
      ),
    );
  }
}
