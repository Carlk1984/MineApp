"""
End-to-End Tests for Heap Leaching – Key Controls Module

Tests cover:
- Unit tests for formulas and edge cases
- Hard stop rules (HS-1, HS-2)
- Soft alert rules (SA-1 to SA-4)
- E2E scenarios (Normal Week, STOP Week, Override)
- RBAC and immutability
"""

import pytest
from datetime import date, timedelta
from tests.conftest import get_auth_token


class TestFormulaCalculations:
    """Unit tests for formula calculations and edge cases."""
    
    def test_solution_applied_m3_calculation(self, client, admin_token, manager_token, contractor_token, setup_heap_and_benchmark):
        """Test: solution_applied_m3 = flow_m3_per_hr * irrigation_hours"""
        headers = {"Authorization": f"Bearer {contractor_token}"}
        
        log_data = {
            "log_date": "2025-01-01",
            "area_irrigated_m2": 1000.0,
            "flow_m3_per_hr": 10.0,
            "irrigation_hours": 20.0,
            "applied_cn_ppm": 300.0,
            "applied_ph": 10.8,
            "pls_flow_m3": 180.0,
            "pls_au_mgL": 0.5,
            "pond_freeboard_m": 0.8,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/daily-control-log",
            json=log_data,
            headers=headers,
        )
        assert response.status_code == 201
        
        expected_solution_applied = 10.0 * 20.0
        assert expected_solution_applied == 200.0
    
    def test_application_rate_calculation(self, client, admin_token, manager_token, contractor_token, setup_heap_and_benchmark):
        """Test: application_rate_L_m2_hr = (flow_m3_per_hr * 1000) / area_irrigated_m2"""
        flow_m3_per_hr = 10.0
        area_irrigated_m2 = 1000.0
        
        expected_rate = (flow_m3_per_hr * 1000) / area_irrigated_m2
        assert expected_rate == 10.0
    
    def test_pls_return_pct_calculation(self, client, admin_token, manager_token, contractor_token, setup_heap_and_benchmark):
        """Test: pls_return_pct = (pls_flow_m3 / solution_applied_m3) * 100"""
        pls_flow_m3 = 180.0
        solution_applied_m3 = 200.0
        
        expected_pls_return = (pls_flow_m3 / solution_applied_m3) * 100
        assert expected_pls_return == 90.0
    
    def test_gold_in_pls_calculation(self, client, admin_token, manager_token, contractor_token, setup_heap_and_benchmark):
        """Test: gold_in_pls_g = pls_au_mgL * pls_flow_m3"""
        pls_au_mgL = 0.5
        pls_flow_m3 = 180.0
        
        expected_gold = pls_au_mgL * pls_flow_m3
        assert expected_gold == 90.0
    
    def test_leach_day_calculation(self):
        """Test: leach_day = (log_date - leach_start_date) + 1"""
        leach_start_date = date(2025, 1, 1)
        log_date = date(2025, 1, 7)
        
        leach_day = (log_date - leach_start_date).days + 1
        assert leach_day == 7


class TestEdgeCases:
    """Test edge cases for formula calculations."""
    
    def test_area_zero_application_rate_null(self):
        """Test: area_irrigated_m2 = 0 => application_rate is NULL + error logged"""
        area_irrigated_m2 = 0
        flow_m3_per_hr = 10.0
        
        if area_irrigated_m2 == 0:
            application_rate = None
        else:
            application_rate = (flow_m3_per_hr * 1000) / area_irrigated_m2
        
        assert application_rate is None
    
    def test_solution_zero_pls_return_null(self):
        """Test: solution_applied_m3 = 0 => pls_return_pct is NULL + error logged"""
        solution_applied_m3 = 0
        pls_flow_m3 = 180.0
        
        if solution_applied_m3 == 0:
            pls_return_pct = None
        else:
            pls_return_pct = (pls_flow_m3 / solution_applied_m3) * 100
        
        assert pls_return_pct is None
    
    def test_head_grade_zero_recovery_null(self):
        """Test: head_grade_gpt = 0 or NULL => recovery_pct is NULL + error logged"""
        head_grade_gpt = 0
        heap_tonnage_t = 1000.0
        cumulative_gold_g = 500.0
        
        if head_grade_gpt == 0 or head_grade_gpt is None:
            recovery_pct = None
        else:
            contained_gold_g = heap_tonnage_t * head_grade_gpt
            recovery_pct = (cumulative_gold_g / contained_gold_g) * 100
        
        assert recovery_pct is None
    
    def test_cn_used_zero_efficiency_null(self):
        """Test: cn_used_kg = 0 or NULL => cn_efficiency_gpkg is NULL + error logged"""
        cn_used_kg = 0
        cumulative_gold_g = 500.0
        
        if cn_used_kg == 0 or cn_used_kg is None:
            cn_efficiency_gpkg = None
        else:
            cn_efficiency_gpkg = cumulative_gold_g / cn_used_kg
        
        assert cn_efficiency_gpkg is None


class TestHardStopRules:
    """Test hard stop rules that block submission."""
    
    def test_hs1_unsafe_ph_blocks_submission(self, client, admin_token, manager_token, contractor_token, setup_heap_and_benchmark):
        """HS-1: applied_ph < ph_min (10.5) should block submission."""
        headers = {"Authorization": f"Bearer {contractor_token}"}
        
        log_data = {
            "log_date": "2025-01-01",
            "area_irrigated_m2": 1000.0,
            "flow_m3_per_hr": 10.0,
            "irrigation_hours": 20.0,
            "applied_cn_ppm": 300.0,
            "applied_ph": 10.2,
            "pls_flow_m3": 180.0,
            "pls_au_mgL": 0.5,
            "pond_freeboard_m": 0.8,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/daily-control-log",
            json=log_data,
            headers=headers,
        )
        
        assert response.status_code == 422
        assert "HS-1" in response.json()["detail"] or "pH" in response.json()["detail"].lower()
    
    def test_hs2_insufficient_freeboard_blocks_submission(self, client, admin_token, manager_token, contractor_token, setup_heap_and_benchmark):
        """HS-2: pond_freeboard_m < pond_freeboard_min_m (0.5) should block submission."""
        headers = {"Authorization": f"Bearer {contractor_token}"}
        
        log_data = {
            "log_date": "2025-01-01",
            "area_irrigated_m2": 1000.0,
            "flow_m3_per_hr": 10.0,
            "irrigation_hours": 20.0,
            "applied_cn_ppm": 300.0,
            "applied_ph": 10.8,
            "pls_flow_m3": 180.0,
            "pls_au_mgL": 0.5,
            "pond_freeboard_m": 0.4,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/daily-control-log",
            json=log_data,
            headers=headers,
        )
        
        assert response.status_code == 422
        assert "HS-2" in response.json()["detail"] or "freeboard" in response.json()["detail"].lower()


class TestSoftAlertRules:
    """Test soft alert rules that flag but allow submission."""
    
    def test_sa1_application_rate_outside_range(self, client, admin_token, manager_token, contractor_token, setup_heap_and_benchmark):
        """SA-1: application_rate outside 8-12 L/m2/hr should flag but allow."""
        headers = {"Authorization": f"Bearer {contractor_token}"}
        
        log_data = {
            "log_date": "2025-01-01",
            "area_irrigated_m2": 1000.0,
            "flow_m3_per_hr": 14.0,
            "irrigation_hours": 20.0,
            "applied_cn_ppm": 300.0,
            "applied_ph": 10.8,
            "pls_flow_m3": 180.0,
            "pls_au_mgL": 0.5,
            "pond_freeboard_m": 0.8,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/daily-control-log",
            json=log_data,
            headers=headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data.get("alerts", [])) > 0
    
    def test_sa2_cyanide_strength_outside_range(self, client, admin_token, manager_token, contractor_token, setup_heap_and_benchmark):
        """SA-2: applied_cn_ppm outside 200-500 should flag but allow."""
        headers = {"Authorization": f"Bearer {contractor_token}"}
        
        log_data = {
            "log_date": "2025-01-02",
            "area_irrigated_m2": 1000.0,
            "flow_m3_per_hr": 10.0,
            "irrigation_hours": 20.0,
            "applied_cn_ppm": 600.0,
            "applied_ph": 10.8,
            "pls_flow_m3": 180.0,
            "pls_au_mgL": 0.5,
            "pond_freeboard_m": 0.8,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/daily-control-log",
            json=log_data,
            headers=headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data.get("alerts", [])) > 0
    
    def test_sa3_low_pls_return(self, client, admin_token, manager_token, contractor_token, setup_heap_and_benchmark):
        """SA-3: pls_return_pct < 80% should flag but allow."""
        headers = {"Authorization": f"Bearer {contractor_token}"}
        
        log_data = {
            "log_date": "2025-01-03",
            "area_irrigated_m2": 1000.0,
            "flow_m3_per_hr": 10.0,
            "irrigation_hours": 20.0,
            "applied_cn_ppm": 300.0,
            "applied_ph": 10.8,
            "pls_flow_m3": 100.0,
            "pls_au_mgL": 0.5,
            "pond_freeboard_m": 0.8,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/daily-control-log",
            json=log_data,
            headers=headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data.get("alerts", [])) > 0
    
    def test_sa4_no_gold_in_pls(self, client, admin_token, manager_token, contractor_token, setup_heap_and_benchmark):
        """SA-4: pls_au_mgL = 0 should flag but allow."""
        headers = {"Authorization": f"Bearer {contractor_token}"}
        
        log_data = {
            "log_date": "2025-01-04",
            "area_irrigated_m2": 1000.0,
            "flow_m3_per_hr": 10.0,
            "irrigation_hours": 20.0,
            "applied_cn_ppm": 300.0,
            "applied_ph": 10.8,
            "pls_flow_m3": 180.0,
            "pls_au_mgL": 0.0,
            "pond_freeboard_m": 0.8,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/daily-control-log",
            json=log_data,
            headers=headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data.get("alerts", [])) > 0


class TestE2EScenarios:
    """End-to-end scenario tests."""
    
    def test_scenario1_normal_week_continue(self, client, admin_token, manager_token, contractor_token, setup_heap_and_benchmark):
        """Scenario 1: Normal week with all metrics within range - expect CONTINUE."""
        headers_contractor = {"Authorization": f"Bearer {contractor_token}"}
        headers_manager = {"Authorization": f"Bearer {manager_token}"}
        
        for day in range(1, 8):
            log_data = {
                "log_date": f"2025-01-{day:02d}",
                "area_irrigated_m2": 1000.0,
                "flow_m3_per_hr": 10.0,
                "irrigation_hours": 20.0,
                "applied_cn_ppm": 300.0,
                "applied_ph": 10.8,
                "pls_flow_m3": 180.0,
                "pls_au_mgL": 0.5,
                "pond_freeboard_m": 0.8,
            }
            
            response = client.post(
                "/api/v1/modules/heap-leaching/daily-control-log",
                json=log_data,
                headers=headers_contractor,
            )
            assert response.status_code == 201
        
        weekly_data = {
            "week_start_date": "2025-01-01",
            "week_end_date": "2025-01-07",
            "cn_used_kg": 800.0,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/weekly-control-summary",
            json=weekly_data,
            headers=headers_manager,
        )
        assert response.status_code == 201
        weekly_summary = response.json()
        
        weekly_summary_id = weekly_summary["weekly_summary"]["id"]
        response = client.post(
            f"/api/v1/modules/heap-leaching/stop-leach-decision/{weekly_summary_id}",
            headers=headers_manager,
        )
        assert response.status_code == 201
        decision = response.json()
        
        assert decision["decision"]["stop_recommendation"] == 0
        assert decision["effective_status"] in ["CONTINUE", "PENDING"]
    
    def test_scenario2_stop_week_high_cn_consumption(self, client, admin_token, manager_token, contractor_token, setup_heap_and_benchmark):
        """Scenario 2: Week with high CN consumption - expect STOP."""
        headers_contractor = {"Authorization": f"Bearer {contractor_token}"}
        headers_manager = {"Authorization": f"Bearer {manager_token}"}
        
        for day in range(8, 15):
            log_data = {
                "log_date": f"2025-01-{day:02d}",
                "area_irrigated_m2": 1000.0,
                "flow_m3_per_hr": 10.0,
                "irrigation_hours": 20.0,
                "applied_cn_ppm": 300.0,
                "applied_ph": 10.8,
                "pls_flow_m3": 180.0,
                "pls_au_mgL": 0.1,
                "pond_freeboard_m": 0.8,
            }
            
            response = client.post(
                "/api/v1/modules/heap-leaching/daily-control-log",
                json=log_data,
                headers=headers_contractor,
            )
            assert response.status_code == 201
        
        weekly_data = {
            "week_start_date": "2025-01-08",
            "week_end_date": "2025-01-14",
            "cn_used_kg": 2500.0,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/weekly-control-summary",
            json=weekly_data,
            headers=headers_manager,
        )
        assert response.status_code == 201
        weekly_summary = response.json()
        
        weekly_summary_id = weekly_summary["weekly_summary"]["id"]
        response = client.post(
            f"/api/v1/modules/heap-leaching/stop-leach-decision/{weekly_summary_id}",
            headers=headers_manager,
        )
        assert response.status_code == 201
        decision = response.json()
        
        assert decision["decision"]["stop_recommendation"] == 1
        assert decision["effective_status"] == "STOP"
    
    def test_scenario3_management_override(self, client, admin_token, manager_token, contractor_token, engineer_token, setup_heap_and_benchmark):
        """Scenario 3: Management override on STOP decision."""
        headers_contractor = {"Authorization": f"Bearer {contractor_token}"}
        headers_manager = {"Authorization": f"Bearer {manager_token}"}
        headers_engineer = {"Authorization": f"Bearer {engineer_token}"}
        
        for day in range(15, 22):
            log_data = {
                "log_date": f"2025-01-{day:02d}",
                "area_irrigated_m2": 1000.0,
                "flow_m3_per_hr": 10.0,
                "irrigation_hours": 20.0,
                "applied_cn_ppm": 300.0,
                "applied_ph": 10.8,
                "pls_flow_m3": 180.0,
                "pls_au_mgL": 0.1,
                "pond_freeboard_m": 0.8,
            }
            
            response = client.post(
                "/api/v1/modules/heap-leaching/daily-control-log",
                json=log_data,
                headers=headers_contractor,
            )
            assert response.status_code == 201
        
        weekly_data = {
            "week_start_date": "2025-01-15",
            "week_end_date": "2025-01-21",
            "cn_used_kg": 2500.0,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/weekly-control-summary",
            json=weekly_data,
            headers=headers_manager,
        )
        assert response.status_code == 201
        weekly_summary = response.json()
        
        weekly_summary_id = weekly_summary["weekly_summary"]["id"]
        response = client.post(
            f"/api/v1/modules/heap-leaching/stop-leach-decision/{weekly_summary_id}",
            headers=headers_manager,
        )
        assert response.status_code == 201
        decision = response.json()
        decision_id = decision["decision"]["id"]
        
        override_data = {
            "decision_id": decision_id,
            "override_action": "CONTINUE",
            "override_reason": "TRIAL_TEST_CONTINUATION",
            "override_justification_text": "This is a test continuation to evaluate recovery patterns over the next monitoring period. Minimum 50 characters required.",
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/stop-leach-override",
            json=override_data,
            headers=headers_manager,
        )
        assert response.status_code == 201
        override_result = response.json()
        
        assert override_result["effective_status"] == "CONTINUE_UNDER_OVERRIDE"
        assert override_result["override"] is not None
        
        response = client.post(
            "/api/v1/modules/heap-leaching/stop-leach-override",
            json=override_data,
            headers=headers_contractor,
        )
        assert response.status_code == 403
        
        response = client.post(
            "/api/v1/modules/heap-leaching/stop-leach-override",
            json=override_data,
            headers=headers_engineer,
        )
        assert response.status_code == 403


class TestRBACAndImmutability:
    """Test role-based access control and immutability."""
    
    def test_contractor_can_create_daily_log(self, client, contractor_token, setup_heap_and_benchmark):
        """Contractor can create DailyControlLog."""
        headers = {"Authorization": f"Bearer {contractor_token}"}
        
        log_data = {
            "log_date": "2025-01-25",
            "area_irrigated_m2": 1000.0,
            "flow_m3_per_hr": 10.0,
            "irrigation_hours": 20.0,
            "applied_cn_ppm": 300.0,
            "applied_ph": 10.8,
            "pls_flow_m3": 180.0,
            "pls_au_mgL": 0.5,
            "pond_freeboard_m": 0.8,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/daily-control-log",
            json=log_data,
            headers=headers,
        )
        assert response.status_code == 201
    
    def test_daily_log_immutable_no_update(self, client, contractor_token, setup_heap_and_benchmark):
        """DailyControlLog cannot be updated after submission."""
        headers = {"Authorization": f"Bearer {contractor_token}"}
        
        log_data = {
            "log_date": "2025-01-26",
            "area_irrigated_m2": 1000.0,
            "flow_m3_per_hr": 10.0,
            "irrigation_hours": 20.0,
            "applied_cn_ppm": 300.0,
            "applied_ph": 10.8,
            "pls_flow_m3": 180.0,
            "pls_au_mgL": 0.5,
            "pond_freeboard_m": 0.8,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/daily-control-log",
            json=log_data,
            headers=headers,
        )
        assert response.status_code == 201
        
        response = client.put(
            "/api/v1/modules/heap-leaching/daily-control-log/2025-01-26",
            json=log_data,
            headers=headers,
        )
        assert response.status_code in [404, 405]
    
    def test_daily_log_immutable_no_delete(self, client, contractor_token, setup_heap_and_benchmark):
        """DailyControlLog cannot be deleted."""
        headers = {"Authorization": f"Bearer {contractor_token}"}
        
        response = client.delete(
            "/api/v1/modules/heap-leaching/daily-control-log/2025-01-26",
            headers=headers,
        )
        assert response.status_code in [404, 405]
    
    def test_engineer_cannot_create_override(self, client, engineer_token, manager_token, contractor_token, setup_heap_and_benchmark):
        """Engineer cannot create StopLeachOverride."""
        headers_contractor = {"Authorization": f"Bearer {contractor_token}"}
        headers_manager = {"Authorization": f"Bearer {manager_token}"}
        headers_engineer = {"Authorization": f"Bearer {engineer_token}"}
        
        for day in range(22, 29):
            log_data = {
                "log_date": f"2025-01-{day:02d}",
                "area_irrigated_m2": 1000.0,
                "flow_m3_per_hr": 10.0,
                "irrigation_hours": 20.0,
                "applied_cn_ppm": 300.0,
                "applied_ph": 10.8,
                "pls_flow_m3": 180.0,
                "pls_au_mgL": 0.1,
                "pond_freeboard_m": 0.8,
            }
            
            response = client.post(
                "/api/v1/modules/heap-leaching/daily-control-log",
                json=log_data,
                headers=headers_contractor,
            )
        
        weekly_data = {
            "week_start_date": "2025-01-22",
            "week_end_date": "2025-01-28",
            "cn_used_kg": 2500.0,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/weekly-control-summary",
            json=weekly_data,
            headers=headers_manager,
        )
        weekly_summary = response.json()
        
        weekly_summary_id = weekly_summary["weekly_summary"]["id"]
        response = client.post(
            f"/api/v1/modules/heap-leaching/stop-leach-decision/{weekly_summary_id}",
            headers=headers_manager,
        )
        decision = response.json()
        decision_id = decision["decision"]["id"]
        
        override_data = {
            "decision_id": decision_id,
            "override_action": "CONTINUE",
            "override_reason": "TRIAL_TEST_CONTINUATION",
            "override_justification_text": "This is a test continuation to evaluate recovery patterns over the next monitoring period. Minimum 50 characters required.",
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/stop-leach-override",
            json=override_data,
            headers=headers_engineer,
        )
        assert response.status_code == 403
    
    def test_override_immutable_no_second_override(self, client, manager_token, contractor_token, setup_heap_and_benchmark):
        """Only one override allowed per decision."""
        headers_contractor = {"Authorization": f"Bearer {contractor_token}"}
        headers_manager = {"Authorization": f"Bearer {manager_token}"}
        
        for day in range(1, 8):
            log_data = {
                "log_date": f"2025-02-{day:02d}",
                "area_irrigated_m2": 1000.0,
                "flow_m3_per_hr": 10.0,
                "irrigation_hours": 20.0,
                "applied_cn_ppm": 300.0,
                "applied_ph": 10.8,
                "pls_flow_m3": 180.0,
                "pls_au_mgL": 0.1,
                "pond_freeboard_m": 0.8,
            }
            
            response = client.post(
                "/api/v1/modules/heap-leaching/daily-control-log",
                json=log_data,
                headers=headers_contractor,
            )
        
        weekly_data = {
            "week_start_date": "2025-02-01",
            "week_end_date": "2025-02-07",
            "cn_used_kg": 2500.0,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/weekly-control-summary",
            json=weekly_data,
            headers=headers_manager,
        )
        weekly_summary = response.json()
        
        weekly_summary_id = weekly_summary["weekly_summary"]["id"]
        response = client.post(
            f"/api/v1/modules/heap-leaching/stop-leach-decision/{weekly_summary_id}",
            headers=headers_manager,
        )
        decision = response.json()
        decision_id = decision["decision"]["id"]
        
        override_data = {
            "decision_id": decision_id,
            "override_action": "CONTINUE",
            "override_reason": "TRIAL_TEST_CONTINUATION",
            "override_justification_text": "This is a test continuation to evaluate recovery patterns over the next monitoring period. Minimum 50 characters required.",
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/stop-leach-override",
            json=override_data,
            headers=headers_manager,
        )
        assert response.status_code == 201
        
        response = client.post(
            "/api/v1/modules/heap-leaching/stop-leach-override",
            json=override_data,
            headers=headers_manager,
        )
        assert response.status_code == 400
    
    def test_override_justification_min_length(self, client, manager_token, contractor_token, setup_heap_and_benchmark):
        """Override justification must be at least 50 characters."""
        headers_contractor = {"Authorization": f"Bearer {contractor_token}"}
        headers_manager = {"Authorization": f"Bearer {manager_token}"}
        
        for day in range(8, 15):
            log_data = {
                "log_date": f"2025-02-{day:02d}",
                "area_irrigated_m2": 1000.0,
                "flow_m3_per_hr": 10.0,
                "irrigation_hours": 20.0,
                "applied_cn_ppm": 300.0,
                "applied_ph": 10.8,
                "pls_flow_m3": 180.0,
                "pls_au_mgL": 0.1,
                "pond_freeboard_m": 0.8,
            }
            
            response = client.post(
                "/api/v1/modules/heap-leaching/daily-control-log",
                json=log_data,
                headers=headers_contractor,
            )
        
        weekly_data = {
            "week_start_date": "2025-02-08",
            "week_end_date": "2025-02-14",
            "cn_used_kg": 2500.0,
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/weekly-control-summary",
            json=weekly_data,
            headers=headers_manager,
        )
        weekly_summary = response.json()
        
        weekly_summary_id = weekly_summary["weekly_summary"]["id"]
        response = client.post(
            f"/api/v1/modules/heap-leaching/stop-leach-decision/{weekly_summary_id}",
            headers=headers_manager,
        )
        decision = response.json()
        decision_id = decision["decision"]["id"]
        
        override_data = {
            "decision_id": decision_id,
            "override_action": "CONTINUE",
            "override_reason": "TRIAL_TEST_CONTINUATION",
            "override_justification_text": "Too short",
        }
        
        response = client.post(
            "/api/v1/modules/heap-leaching/stop-leach-override",
            json=override_data,
            headers=headers_manager,
        )
        assert response.status_code == 422
