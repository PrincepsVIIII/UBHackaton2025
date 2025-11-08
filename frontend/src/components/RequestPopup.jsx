import PropTypes from "prop-types";

function formatDistance(distanceKm) {
  if (distanceKm == null) return "Unknown distance";
  if (distanceKm < 1) {
    return `${(distanceKm * 1000).toFixed(0)} m`;
  }
  return `${distanceKm.toFixed(1)} km`;
}

function RequestPopup({ request, score, distanceKm, onClaim, isClaiming, errorMessage }) {
  const urgencyLabel = request.urgency_level.charAt(0).toUpperCase() + request.urgency_level.slice(1);

  return (
    <div className="request-popup">
      <h3>{request.title}</h3>
      <p>{request.description}</p>
      <dl>
        <div>
          <dt>Urgency</dt>
          <dd>{urgencyLabel}</dd>
        </div>
        <div>
          <dt>Distance</dt>
          <dd>{formatDistance(distanceKm)}</dd>
        </div>
        <div>
          <dt>Score</dt>
          <dd>{score.toFixed(2)}</dd>
        </div>
      </dl>
      {errorMessage && <p className="popup-error">{errorMessage}</p>}
      <button type="button" onClick={onClaim} disabled={isClaiming}>
        {isClaiming ? "Claiming…" : "Claim Request"}
      </button>
    </div>
  );
}

RequestPopup.propTypes = {
  request: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
    urgency_level: PropTypes.string.isRequired,
  }).isRequired,
  score: PropTypes.number.isRequired,
  distanceKm: PropTypes.number,
  onClaim: PropTypes.func.isRequired,
  isClaiming: PropTypes.bool,
  errorMessage: PropTypes.string,
};

RequestPopup.defaultProps = {
  distanceKm: null,
  isClaiming: false,
  errorMessage: null,
};

export default RequestPopup;

