import axios from '../api/api';

function RequestCard({ request, refresh }) {
  const handleAction = async (action) => {
    try {
      await axios.post(`/requests/${request.id}/${action}`);
      refresh();
    } catch(err) {
      alert('Action failed');
    }
  };

  return (
    <div className="request-card">
      <h4>{request.address}</h4>
      <p>{request.description}</p>
      <p>Status: {request.status}</p>
      {request.status === 'pending' && (
        <>
          <button onClick={()=>handleAction('accept')}>Accept</button>
          <button onClick={()=>handleAction('decline')}>Decline</button>
        </>
      )}
    </div>
  );
}

export default RequestCard;
