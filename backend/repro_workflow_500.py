"""Reproduce workflow 500 by calling service directly."""
import asyncio
import os
import sys
import traceback

# Set secret key
os.environ['WEBUI_SECRET_KEY'] = open('.webui_secret_key').read().strip()

async def main():
    from open_webui.pm.models.workflow import Workflows, WorkflowModel
    from open_webui.pm.services.workflow_service import WorkflowService

    # Known workflow IDs from DB
    test_ids = [
        '6f2ee592-1982-4294-bc93-fac8cd43ed41',
        'c4c61c4d-8a2a-4537-806a-fa328f797c6a',
        '3777552a-460a-4e63-ac77-b6588c49d386',
    ]

    for wid in test_ids:
        print(f"\n=== Testing workflow_id: {wid} ===")
        # Step 1: Direct model fetch
        try:
            wf = await Workflows.get_workflow_by_id(wid)
            print(f"  Workflows.get_workflow_by_id: OK, type={type(wf).__name__}")
            if wf:
                print(f"    id={wf.id}, name={wf.name}, status={wf.status}")
                print(f"    nodes={wf.nodes[:100] if wf.nodes else 'None'}")
                print(f"    edges={wf.edges[:100] if wf.edges else 'None'}")
        except Exception as e:
            print(f"  Workflows.get_workflow_by_id FAILED: {type(e).__name__}: {e}")
            traceback.print_exc()
            continue

        # Step 2: Service layer (returns dict via model_dump)
        try:
            d = await WorkflowService.get_workflow(wid)
            print(f"  WorkflowService.get_workflow: OK, type={type(d).__name__}")
            if d:
                print(f"    keys={list(d.keys())}")
                print(f"    nodes type={type(d.get('nodes'))}, value={str(d.get('nodes'))[:100]}")
        except Exception as e:
            print(f"  WorkflowService.get_workflow FAILED: {type(e).__name__}: {e}")
            traceback.print_exc()
            continue

        # Step 3: _parse_workflow_json (from router)
        try:
            from open_webui.routers.workflows import _parse_workflow_json
            d2 = dict(d) if d else None
            result = _parse_workflow_json(d2)
            print(f"  _parse_workflow_json: OK, nodes type={type(result.get('nodes'))}, len={len(result.get('nodes', []))}")
        except Exception as e:
            print(f"  _parse_workflow_json FAILED: {type(e).__name__}: {e}")
            traceback.print_exc()

asyncio.run(main())
