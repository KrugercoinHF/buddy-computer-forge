const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const schemaDir = path.join(__dirname, '..', 'schemas', 'integration');
const schemaFiles = [
  'work-request.schema.json',
  'event-envelope.schema.json',
  'approval-record.schema.json',
];

test('Buddy Agency integration schemas are valid JSON and versioned', () => {
  for (const filename of schemaFiles) {
    const schema = JSON.parse(fs.readFileSync(path.join(schemaDir, filename), 'utf8'));
    assert.equal(schema.$schema, 'https://json-schema.org/draft/2020-12/schema');
    assert.equal(schema.type, 'object');
    assert.equal(schema.additionalProperties, false);
    assert.equal(schema.properties.schema_version.const, '1.0.0');
    assert.ok(Array.isArray(schema.required) && schema.required.length > 0);
    for (const field of schema.required) {
      assert.ok(Object.hasOwn(schema.properties, field), `${filename}: required field ${field} has no property definition`);
    }
  }
});

test('approval schema binds an approval to an exact request digest and explicit decision', () => {
  const schema = JSON.parse(fs.readFileSync(path.join(schemaDir, 'approval-record.schema.json'), 'utf8'));
  assert.deepEqual(schema.properties.decision.enum, ['approved', 'denied', 'revoked']);
  assert.equal(schema.properties.request_digest.pattern, '^[a-f0-9]{64}$');
  assert.ok(schema.required.includes('action'));
  assert.ok(schema.required.includes('target'));
  assert.ok(schema.required.includes('scope'));
});
