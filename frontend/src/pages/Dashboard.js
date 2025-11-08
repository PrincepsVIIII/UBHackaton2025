import { useState, useEffect } from 'react';
import axios from '../api/api';
import RequestCard from '../components/RequestCard';

function Dashboard() {
  const [requests, setRequests] = useState([]);

  const fetchRequests = async () => {
    const res = await axios.get('/requests');
    setRequests(res.data);
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  return (
    <div>
      <h2>Dashboard</h2>
      {requests.map(req => (
        <RequestCard key={req.id} request={req} refresh={fetchRequests} />
      ))}
    </div>
  );
}

export default Dashboard;
