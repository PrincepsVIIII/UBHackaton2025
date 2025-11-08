function ScoreLegend() {
  return (
    <aside className="score-legend">
      <h4>Priority</h4>
      <ul>
        <li>
          <span className="legend-dot legend-dot--high" />
          High score
        </li>
        <li>
          <span className="legend-dot legend-dot--medium" />
          Medium score
        </li>
        <li>
          <span className="legend-dot legend-dot--low" />
          Low score
        </li>
      </ul>
    </aside>
  );
}

export default ScoreLegend;

