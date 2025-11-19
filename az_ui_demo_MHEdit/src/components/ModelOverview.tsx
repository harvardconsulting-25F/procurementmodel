function ModelOverview() {
  return (
    <section className="bg-white rounded-lg shadow-md p-6 border-l-4 border-primary space-y-5">
      <div>
        <h2 className="text-xl font-semibold text-primary">How does the model work?</h2>
        <p className="text-gray-600 mt-2">
          The model analyzes upstream supplier inputs to predict how bioresin suppliers will choose to price their product.
          When raw materials or other inputs increase, suppliers generally raise prices to compensate. To capture real-world
          decision making, the model weighs multiple input costs instead of relying on a single driver.
        </p>
      </div>

      <div className="space-y-3">
        <p className="text-gray-600">
          External datasets track month-over-month input cost changes across four categories:
        </p>
        <ul className="list-disc list-inside text-gray-600 space-y-1">
          <li>
            <strong>Labor input:</strong> employee payroll costs drawn from COGS and SG&amp;A
          </li>
          <li>
            <strong>Capital input:</strong> factories, equipment, PP&amp;E, and other long-lived assets
          </li>
          <li>
            <strong>Materials input:</strong> raw materials, primarily sourced from COGS
          </li>
          <li>
            <strong>Energy input:</strong> electricity and power expenses, mostly within COGS
          </li>
        </ul>
        <p className="text-gray-600">
          Using historical regression and microeconomic modeling, the system correlates these inputs with bioresin prices to
          project future pricing. The full pipeline is automated, but users can override assumptions with manual weights.
        </p>
      </div>

      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-primary">Manual weights</h3>
        <p className="text-gray-600">
          Three optional weight types let you encode custom knowledge about a supplier or market condition:
        </p>
        <ul className="list-disc list-inside text-gray-600 space-y-1">
          <li>
            <strong>Category weights:</strong> override the algorithm&apos;s industry averages if a supplier relies more (or less)
            on certain inputs.
          </li>
          <li>
            <strong>Optimism weights:</strong> reflect sentiment or proprietary intel the market may not yet price in.
          </li>
          <li>
            <strong>Extraneous events:</strong> directly adjust the forecast when one-off shocks fall outside the four inputs.
          </li>
        </ul>
      </div>
    </section>
  );
}

export default ModelOverview;

