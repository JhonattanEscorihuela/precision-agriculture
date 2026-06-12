"""
Test script to emulate user workflow: draw polygon → select date → acquire.
Diagnoses timing/race condition issues.
"""

import asyncio
import httpx
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Test coordinates (Parcela 211)
PARCELA_211 = [
    [-67.528058, 8.8441233],
    [-67.5153475, 8.8386166],
    [-67.5103962, 8.8478932],
    [-67.522828, 8.8534209],
    [-67.528058, 8.8441233]
]

BASE_URL = "http://localhost:8000"


async def test_full_workflow():
    """
    Emulate complete user workflow:
    1. Create/get polygon
    2. Query available dates
    3. Acquire bands for a date (FIRST ATTEMPT - might fail)
    4. Retry if failed (should succeed)
    """

    async with httpx.AsyncClient(timeout=120.0) as client:
        print("\n" + "="*80)
        print("TEST: USER WORKFLOW - Draw Polygon → Select Date → Acquire")
        print("="*80)

        # Step 1: Use existing polygon (ID=5 from previous tests)
        print("\n🗺️  Step 1: Using existing polygon...")
        polygon_id = 5  # From previous successful acquisitions
        print(f"✅ Using polygon ID={polygon_id}")

        # Step 2: Query available dates (simulating opening SentinelPanel)
        print(f"\n📅 Step 2: Query available dates for polygon {polygon_id}...")
        try:
            dates_response = await client.get(
                f"{BASE_URL}/api/sentinel/available-dates/{polygon_id}?start_date=2025-12-01&end_date=2026-06-12&max_cloud=20"
            )
            dates_response.raise_for_status()
            dates_data = dates_response.json()
            available_dates = dates_data.get("dates", [])

            print(f"✅ Found {len(available_dates)} available dates")

            if not available_dates:
                print("❌ No dates available for testing")
                return

            # Pick first date that hasn't been acquired
            target_date = None
            for date_info in available_dates:
                if not date_info.get("acquired", False):
                    target_date = date_info["date"]
                    break

            if not target_date:
                print("⚠️  All dates already acquired, using first one")
                target_date = available_dates[0]["date"]

            print(f"🎯 Selected date: {target_date}")

        except Exception as e:
            print(f"❌ Error fetching dates: {e}")
            return

        # Step 3: FIRST ATTEMPT - Acquire bands (this is where bug happens)
        print(f"\n🚀 Step 3a: FIRST ATTEMPT - Acquire bands for {target_date}...")
        first_attempt_success = False

        try:
            acquire_response = await client.post(
                f"{BASE_URL}/api/sentinel/acquire",
                json={
                    "polygon_id": polygon_id,
                    "date": target_date
                }
            )

            print(f"   Status: {acquire_response.status_code}")

            if acquire_response.status_code == 200:
                acquire_data = acquire_response.json()
                print(f"✅ FIRST ATTEMPT SUCCEEDED!")
                print(f"   acquisition_id: {acquire_data.get('acquisition_id')}")
                print(f"   already_existed: {acquire_data.get('already_existed', False)}")
                first_attempt_success = True
            else:
                error_detail = acquire_response.json().get("detail", "Unknown error")
                print(f"❌ FIRST ATTEMPT FAILED: {error_detail}")

        except Exception as e:
            print(f"❌ FIRST ATTEMPT EXCEPTION: {e}")

        # Step 4: RETRY (if first failed) - User clicks "Reintentar"
        if not first_attempt_success:
            print(f"\n🔄 Step 3b: RETRY - User clicks 'Reintentar'...")

            # Small delay (simulating user clicking retry button)
            await asyncio.sleep(0.5)

            try:
                retry_response = await client.post(
                    f"{BASE_URL}/api/sentinel/acquire",
                    json={
                        "polygon_id": polygon_id,
                        "date": target_date
                    }
                )

                print(f"   Status: {retry_response.status_code}")

                if retry_response.status_code == 200:
                    retry_data = retry_response.json()
                    print(f"✅ RETRY SUCCEEDED!")
                    print(f"   acquisition_id: {retry_data.get('acquisition_id')}")
                    print(f"   already_existed: {retry_data.get('already_existed', False)}")

                    print("\n" + "="*80)
                    print("🐛 BUG CONFIRMED: First attempt fails, retry succeeds")
                    print("="*80)
                else:
                    error_detail = retry_response.json().get("detail", "Unknown error")
                    print(f"❌ RETRY ALSO FAILED: {error_detail}")

            except Exception as e:
                print(f"❌ RETRY EXCEPTION: {e}")

        print("\n" + "="*80)
        print("TEST COMPLETE")
        print("="*80)


if __name__ == "__main__":
    asyncio.run(test_full_workflow())
