// frontend/src/pages/RequestForm.js
import React, { useState } from 'react';

function RequestForm() {
  const [address, setAddress] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    alert(`Request submitted:\nAddress: ${address}\nDescription: ${description}`);
    setAddress('');
    setDescription('');
  };

  return (
    <div>
      <h2>Submit a Service Request</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Address: </label>
          <input value={address} onChange={(e) => setAddress(e.target.value)} required />
        </div>
        <div>
          <label>Description: </label>
          <input value={description} onChange={(e) => setDescription(e.target.value)} required />
        </div>
        <button type="submit">Submit</button>
      </form>
    </div>
  );
}

export default RequestForm;
