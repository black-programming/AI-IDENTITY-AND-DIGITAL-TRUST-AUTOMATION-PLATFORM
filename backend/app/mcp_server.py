"""Model Context Protocol (MCP) Server for AI Identity & Digital Trust Platform.

Exposes identity verification, document extraction (YOLO & OCR), and regulatory
validation tools over standard I/O (stdio transport) for AI assistants (Cursor,
Claude Desktop, Antigravity, etc.).
"""

import json
import os
import sys
from typing import Any, Dict

# Ensure backend directory is in python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.dvla_service import (
    validate_dvla_licence_number,
    get_dvla_benchmarks,
)
from app.services.pancard_service import validate_pan_number, mask_pan_number
from app.services.aadhaar_service import (
    validate_aadhaar_number,
    mask_aadhaar_number,
)


TOOLS = [
    {
        "name": "verify_driving_licence",
        "description": "Validates a UK or Indian driving licence number against statutory syntax, gender/DOB encoding, and check digits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "licence_number": {
                    "type": "string",
                    "description": "Full driving licence number (e.g. SMITH705281J99AA or TN68 20120003562)",
                },
                "surname": {
                    "type": "string",
                    "description": "Applicant surname for cross-consistency check",
                },
                "gender": {
                    "type": "string",
                    "enum": ["MALE", "FEMALE", "OTHER"],
                    "description": "Applicant gender",
                },
                "dob": {
                    "type": "string",
                    "description": "Date of Birth (YYYY-MM-DD or DD/MM/YYYY)",
                },
            },
            "required": ["licence_number"],
        },
    },
    {
        "name": "verify_pan_card",
        "description": "Validates an Indian PAN (Permanent Account Number) according to Income Tax Dept 10-character syntax, entity classification, and surname initial matching.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pan_number": {
                    "type": "string",
                    "description": "10-character alphanumeric PAN (e.g. ABCPS1234F)",
                },
                "surname": {
                    "type": "string",
                    "description": "Applicant surname to verify 5th character consistency",
                },
            },
            "required": ["pan_number"],
        },
    },
    {
        "name": "verify_aadhaar_card",
        "description": "Validates a 12-digit Indian Aadhaar number using the UIDAI Verhoeff dihedral group check digit algorithm.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "aadhaar_number": {
                    "type": "string",
                    "description": "12-digit Aadhaar number (e.g. 9123 4567 8912)",
                },
            },
            "required": ["aadhaar_number"],
        },
    },
    {
        "name": "get_dvla_national_benchmarks",
        "description": "Retrieves official UK DVLA demographic distributions (46M+ records by age, gender, and postcode district) for prior risk assessment.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "extract_document_sample_entities",
        "description": "Simulates / returns localized YOLO entity bounding box extractions for known test dataset samples (e.g. tnarun.jpeg, Texas.jpg).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sample_id": {
                    "type": "string",
                    "enum": ["tnarun", "texas", "rajesh_pan", "priya_aadhaar"],
                    "description": "Dataset sample identifier",
                },
            },
            "required": ["sample_id"],
        },
    },
]


def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "verify_driving_licence":
        licence = arguments.get("licence_number", "")
        surname = arguments.get("surname")
        gender = arguments.get("gender")
        dob = arguments.get("dob")
        res = validate_dvla_licence_number(
            licence_num=licence,
            applicant_surname=surname,
            applicant_gender=gender,
            applicant_dob=dob,
        )
        return {
            "status": "success",
            "licence_number_masked": res.get("masked_number"),
            "is_valid": res.get("is_valid"),
            "details": res,
        }

    elif tool_name == "verify_pan_card":
        pan = arguments.get("pan_number", "").strip().upper()
        surname = arguments.get("surname")
        res = validate_pan_number(raw_pan=pan, applicant_surname=surname)
        return {
            "status": "success",
            "pan_masked": res.get("masked_number"),
            "is_valid": res.get("is_valid"),
            "holder_type": res.get("holder_type_description"),
            "surname_match": res.get("surname_match"),
            "details": res,
        }

    elif tool_name == "verify_aadhaar_card":
        aadhaar = arguments.get("aadhaar_number", "")
        res = validate_aadhaar_number(raw_number=aadhaar)
        return {
            "status": "success",
            "aadhaar_masked": res.get("masked_number"),
            "is_valid": res.get("is_valid"),
            "algorithm": "UIDAI Verhoeff D5",
            "details": res,
        }

    elif tool_name == "get_dvla_national_benchmarks":
        benchmarks = get_dvla_benchmarks()
        return {
            "status": "success",
            "dataset": benchmarks.get("dataset_name"),
            "jurisdiction": benchmarks.get("jurisdiction"),
            "summary": benchmarks.get("summary"),
        }

    elif tool_name == "extract_document_sample_entities":
        sample_id = arguments.get("sample_id", "tnarun")
        if sample_id == "tnarun":
            return {
                "document": "Driving Licence (India — Tamil Nadu TN68)",
                "filename": "tnarun.jpeg",
                "classes_detected": 8,
                "entities": {
                    "name": "ARUN PRASATH B",
                    "license_number": "TN68 20120003562",
                    "dob": "13/12/1992",
                    "issue_date": "06/06/2012",
                    "address": "Mela Korukkai, Kumbakonam TK",
                },
                "confidence_avg": 0.97,
            }
        elif sample_id == "texas":
            return {
                "document": "Driving Licence (United States — Texas)",
                "filename": "Texas.jpg",
                "entities": {
                    "name": "SAMPLEQa. JOHN",
                    "license_number": "000000194",
                    "address": "12612 River Hills, Aspen, TX 12345",
                },
                "confidence_avg": 0.96,
            }
        else:
            return {
                "sample_id": sample_id,
                "status": "verified",
                "confidence": 0.99,
            }

    return {"error": f"Unknown tool: {tool_name}"}


def main():
    """Main JSON-RPC stdio loop for MCP clients."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            msg = json.loads(line)
            method = msg.get("method")
            msg_id = msg.get("id")

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                        },
                        "serverInfo": {
                            "name": "ai-identity-verification-mcp",
                            "version": "1.0.0",
                        },
                    },
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            elif method == "notifications/initialized":
                # Notification, no response required
                pass

            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": TOOLS,
                    },
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            elif method == "tools/call":
                params = msg.get("params", {})
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                tool_result = handle_tool_call(tool_name, arguments)

                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(tool_result, indent=2),
                            }
                        ]
                    },
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            elif method == "ping":
                response = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found",
                    },
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

        except Exception as e:
            err_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": str(e),
                },
            }
            sys.stdout.write(json.dumps(err_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
