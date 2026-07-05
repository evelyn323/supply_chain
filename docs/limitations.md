# Limitations
The project does not include the following
- Supplier capacity constraints
- Multi-echelon inventory networks
- Product substitution
- Quantity discounts
- Dynamic pricing
- Real-time production scheduling
- Backorders
- Multi-store optimization

The project also relies on observed sales rather than true latent demand, with additional dataset-specific limitations documented in the data ingestion notes.

The MVP also does not model price or promotion effects directly inside the simulator. These may be considered later through forecasting covariates.

The current simulator starts each run with no outstanding orders. This can disadvantage longer-lead-time policies near the beginning of the evaluation window, so lead-time sensitivity analysis is used to assess how much this startup assumption matters.

A later extension could carry simulator state forward from an unscored train-period warm-up into validation or test so that scored windows begin with a more realistic inventory pipeline.
