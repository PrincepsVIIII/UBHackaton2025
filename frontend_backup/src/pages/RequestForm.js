import { useState } from 'react';
import axios from '../api/api';

function RequestForm() {
  const [address, setAddress] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/requests', { address, description });
      alert('Request submitted!');
      setAddress('');
      setDescription('');
    } catch(err) {
      alert(err.response?.data?.message || 'Error submitting request');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input placeholder="Address" value={address} onChange={e => setAddress(e.target.value)} required />
      <textarea placeholder="Description" value={description} onChange={e => setDescription(e.target.value)} required />
      <button type="submit">Submit Request</button>
    </form>
  );
}

export default RequestForm;
