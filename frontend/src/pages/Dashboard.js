// frontend/src/pages/Dashboard.js
import React, { useState } from 'react';

function Dashboard() {
  const [requests] = useState([
    { id: 1, address: '123 Main St', description: 'Fix sink', status: 'pending' },
    { id: 2, address: '456 Elm St', description: 'Paint wall', status: 'accepted' },
  ]);

  return (
    <div>
      <h2>Dashboard</h2>
      {requests.map((req) => (
        <div key={req.id} style={{ border: '1px solid black', margin: '10px', padding: '10px' }}>
          <p><strong>Address:</strong> {req.address}</p>
          <p><strong>Description:</strong> {req.description}</p>
          <p><strong>Status:</strong> {req.status}</p>
        </div>
      ))}
    </div>
  );
}

export default Dashboard;
