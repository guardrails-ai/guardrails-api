AUDIT_FUNCTION_REV_NONE = """
CREATE OR REPLACE FUNCTION guard_audit_function() RETURNS TRIGGER AS $guard_audit$
BEGIN
    IF (TG_OP = 'DELETE') THEN
    INSERT INTO guards_audit SELECT gen_random_uuid(), OLD.*, now(), 'D';
    ELSIF (TG_OP = 'UPDATE') THEN
    INSERT INTO guards_audit SELECT gen_random_uuid(), OLD.*, now(), 'U';
    ELSIF (TG_OP = 'INSERT') THEN
    INSERT INTO guards_audit SELECT gen_random_uuid(), NEW.*, now(), 'I';
    END IF;
    RETURN null;
END;
$guard_audit$
LANGUAGE plpgsql;
"""

AUDIT_TRIGGER_REV_NONE = """
DROP TRIGGER IF EXISTS guard_audit_trigger
  ON guards;
CREATE TRIGGER guard_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON guards
    FOR EACH ROW
    EXECUTE PROCEDURE guard_audit_function();
"""

AUDIT_FUNCTION_REV_608f976c28d4 = """
CREATE OR REPLACE FUNCTION guard_audit_function() RETURNS TRIGGER AS $guard_audit$
BEGIN
    IF (TG_OP = 'DELETE') THEN
    INSERT INTO guards_audit
    (id, name, guard, guard_id, created_by, created_at, updated_by, updated_at, replaced_on, operation)
    SELECT gen_random_uuid(), OLD.name, OLD.guard, OLD.id, OLD.created_by, OLD.created_at, OLD.updated_by, OLD.updated_at, now(), 'D';
    ELSIF (TG_OP = 'UPDATE') THEN
    INSERT INTO guards_audit
    (id, name, guard, guard_id, created_by, created_at, updated_by, updated_at, replaced_on, operation)
    SELECT gen_random_uuid(), OLD.name, OLD.guard, OLD.id, OLD.created_by, OLD.created_at, OLD.updated_by, OLD.updated_at, now(), 'U';
    ELSIF (TG_OP = 'INSERT') THEN
    INSERT INTO guards_audit
    (id, name, guard, guard_id, created_by, created_at, updated_by, updated_at, replaced_on, operation)
    SELECT gen_random_uuid(), NEW.name, NEW.guard, NEW.id, NEW.created_by, NEW.created_at, NEW.updated_by, NEW.updated_at, now(), 'I';
    END IF;
    RETURN null;
END;
$guard_audit$
LANGUAGE plpgsql;
"""

AUDIT_TRIGGER_REV_608f976c28d4 = """
DROP TRIGGER IF EXISTS guard_audit_trigger
  ON guards;
CREATE TRIGGER guard_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON guards
    FOR EACH ROW
    EXECUTE PROCEDURE guard_audit_function();
"""
