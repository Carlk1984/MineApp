import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../services/hive_service.dart';
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
  bool _isSubmitting = false;
  bool _isOffline = false;

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
      _controllers[field['key']] = TextEditingController();
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
        ];
      case 'Extraction':
        return [
          {'key': 'ore_extracted', 'label': 'Ore Extracted (tons)', 'type': 'number', 'required': true},
          {'key': 'waste_removed', 'label': 'Waste Removed (tons)', 'type': 'number', 'required': true},
          {'key': 'equipment_hours', 'label': 'Equipment Operating Hours', 'type': 'number', 'required': true},
          {'key': 'fuel_consumption', 'label': 'Fuel Consumption (L)', 'type': 'number', 'required': true},
          {'key': 'safety_incidents', 'label': 'Safety Incidents', 'type': 'number', 'required': true},
          {'key': 'weather_conditions', 'label': 'Weather Conditions', 'type': 'select', 'options': ['Clear', 'Rainy', 'Windy', 'Stormy'], 'required': true},
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
        ];
      case 'Materials & Assets':
        return [
          {'key': 'inventory_count', 'label': 'Inventory Items Counted', 'type': 'number', 'required': true},
          {'key': 'new_acquisitions', 'label': 'New Equipment/Materials', 'type': 'text', 'required': false},
          {'key': 'maintenance_completed', 'label': 'Maintenance Tasks Completed', 'type': 'number', 'required': true},
          {'key': 'asset_condition', 'label': 'Overall Asset Condition', 'type': 'select', 'options': ['Excellent', 'Good', 'Fair', 'Poor'], 'required': true},
          {'key': 'replacement_needed', 'label': 'Equipment Needing Replacement', 'type': 'text', 'required': false},
          {'key': 'cost_tracking', 'label': 'Cost Tracking Notes', 'type': 'text', 'required': false},
        ];
      default:
        return [];
    }
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
      default:
        return const SizedBox.shrink();
    }
  }

  void _collectFormData() {
    final fields = _getFormFields();
    for (var field in fields) {
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

  Future<void> _submitForm() async {
    if (!_formKey.currentState!.validate()) return;

    _collectFormData();
    
    setState(() {
      _isSubmitting = true;
    });

    try {
      final authService = Provider.of<AuthService>(context, listen: false);
      final apiService = Provider.of<ApiService>(context, listen: false);
      
      _formData['manager_on_duty'] = 'Manager Name';
      
      final record = Record(
        id: '',
        module: widget.moduleName,
        data: _formData,
        managerOnDuty: _formData['manager_on_duty'],
        submittedBy: authService.currentUser?.id ?? '',
        approvalStatus: 'pending',
        timestamp: DateTime.now(),
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
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            ...formFields.map((field) => Padding(
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
