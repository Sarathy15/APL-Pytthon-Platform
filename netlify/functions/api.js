let migrationJobs = [];

function jsonResponse(statusCode, payload, extraHeaders = {}) {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type',
      ...extraHeaders,
    },
    body: JSON.stringify(payload),
  };
}

exports.handler = async (event) => {
  const path = event.path || '';
  const method = event.httpMethod || 'GET';

  if (method === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      },
      body: '',
    };
  }

  if (method === 'GET' && path === '/api/health') {
    return jsonResponse(200, { status: 'ok', service: 'APL-Migration-Backend' });
  }

  if (method === 'GET' && path === '/api/jobs') {
    return jsonResponse(200, migrationJobs);
  }

  if (method === 'POST' && path === '/api/jobs') {
    const body = event.body ? JSON.parse(event.body) : {};
    const job = {
      id: `JOB-${Date.now()}`,
      status: 'pending',
      createdAt: new Date().toISOString(),
      ...body,
    };
    migrationJobs.push(job);
    return jsonResponse(201, job);
  }

  return jsonResponse(404, { error: 'Not found' });
};
