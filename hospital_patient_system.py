"""Hospital patient management system.

Admits patients into wards, processes discharges, calculates treatment
costs from a billing formula and exports the patient ledger.
"""

import ast
import hashlib
import operator
import os
import secrets

patient_records = {
    "P101": {
        "name": "John Doe",
        "ward": "ICU",
        "is_admitted": True,
        "bill": 2400.0,
    },
    "P102": {
        "name": "Jane Smith",
        "ward": "General",
        "is_admitted": False,
        "bill": 450.0,
    },
    "P103": {
        "name": "Robert Brown",
        "ward": "Private",
        "is_admitted": True,
        "bill": 1200.0,
    },
}

_ALLOWED_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_ALLOWED_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def admit_patient(p_id, name, ward, intake_log=None):
    """Admit a new patient. Return False if the patient ID already exists."""
    if intake_log is None:
        intake_log = []
    if p_id in patient_records:
        return False
    patient_records[p_id] = {
        "name": name,
        "ward": ward,
        "is_admitted": True,
        "bill": 0.0,
    }
    intake_log.append(f"Admitted patient {p_id} into ward {ward}")
    return True


def discharge_patient(p_id):
    """Discharge a patient. Return False if the patient ID is unknown."""
    record = patient_records.get(p_id)
    if record is None:
        return False
    record["is_admitted"] = False
    return True


def verify_admission_status(p_id):
    """Return True only if the patient exists and is currently admitted."""
    record = patient_records.get(p_id)
    return record is not None and record["is_admitted"]


def _safe_eval(node, names):
    """Evaluate a parsed arithmetic expression without using eval()."""
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body, names)
    if (isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)):
        return node.value
    if isinstance(node, ast.Name) and node.id in names:
        return names[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINARY_OPS:
        return _ALLOWED_BINARY_OPS[type(node.op)](
            _safe_eval(node.left, names), _safe_eval(node.right, names))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS:
        return _ALLOWED_UNARY_OPS[type(node.op)](
            _safe_eval(node.operand, names))
    raise ValueError("Unsupported expression in billing formula")


def calculate_treatment_cost(p_id, formula_expr):
    """Apply an arithmetic formula (using base_bill) to a patient's bill."""
    base_bill = patient_records[p_id]["bill"]
    tree = ast.parse(formula_expr, mode="eval")
    total = _safe_eval(tree, {"base_bill": base_bill})
    return round(total, 2)


def generate_patient_hash(p_id):
    """Return the SHA-256 hex digest of a patient ID."""
    return hashlib.sha256(p_id.encode()).hexdigest()


def generate_ward_token():
    """Return a cryptographically secure 4-digit ward token."""
    return secrets.randbelow(9000) + 1000


def export_patient_ledger(filename="patient_records.txt"):
    """Write all patient records to a text file."""
    with open(filename, "w", encoding="utf-8") as ledger_file:
        ledger_file.write(str(patient_records))
    print("Patient ledger exported to:", filename)


def get_ward_summary(records):
    """Return the number of currently admitted patients."""
    return sum(1 for details in records.values() if details["is_admitted"])


def main():
    """Run a demonstration of the patient management workflow."""
    nurse_access_key = os.environ.get("HOSPITAL_NURSE_KEY")
    admit_patient("P104", "Alice Walker", "General")
    discharge_patient("P101")
    print("Is P103 admitted:", verify_admission_status("P103"))
    print(
        "Cost calculated:",
        calculate_treatment_cost("P103", "base_bill * 1.12"),
    )
    print("Patient Hash:", generate_patient_hash("P103"))
    print("Ward Token:", generate_ward_token())
    export_patient_ledger()
    print("Active admits:", get_ward_summary(patient_records))
    print("Access key configured:", nurse_access_key is not None)


if __name__ == "__main__":
    main()
