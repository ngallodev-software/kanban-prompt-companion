export class ApiError extends Error {
  readonly name = "ApiError";

  constructor(
    public readonly status: number,
    message: string,
    public readonly retryable: boolean,
    public readonly cause?: unknown,
  ) {
    super(message);
    Object.setPrototypeOf(this, new.target.prototype);
  }
}
