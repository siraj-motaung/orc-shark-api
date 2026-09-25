# ChatGPT and GitHub Copilot Usage and Methodology

## Tools I used and how I used them

#### Tools used - ChatGPT and GitHub Copilot.

I used ChatGPT and GitHub Copilot throughout the project as thinking partners, research assistants, and review tools. My goal was not to outsource the work, but to sharpen my own reasoning, test assumptions, and get perspective on technical trade-offs before making decisions.

I did not treat ChatGPT or GitHub Copilot output as authoritative or as a substitute for engineering judgment. I used them to explore ideas, compare approaches, challenge my assumptions, and help structure my thinking. I remained responsible for the final architecture, implementation choices, code changes, validation, and overall direction of the project.

---

### 1. Architecture and Design Exploration

I used ChatGPT and GitHub Copilot to test whether the architecture I was considering was appropriate for a small FastAPI application within a tight timebox. I was not asking either tool to define the system for me; I was using them to reason through design options and confirm whether my own ideas were sound.

Some of the questions I used to guide my own decisions included:
* Is a simple `API → Service → Database` structure appropriate for this project?
* Would adding a repository layer provide real value, or would it introduce unnecessary abstraction?
* Is a generic repository pattern justified here, or is it over-engineering for this scope?
* Where should business logic live so the code remains clear and testable?
* How much separation of concerns is appropriate for a 6–8 hour assignment?
* At what point does a design decision start to add complexity without delivering clear value?

The purpose was to evaluate trade-offs, not to accept a default pattern as the “correct” answer.

This helped me settle on a relatively simple design:
$$\text{API Route} \longrightarrow \text{Service} \longrightarrow \text{SQLAlchemy} \longrightarrow \text{PostgreSQL}$$

while keeping the responsibilities clear and avoiding unnecessary complexity.

---

### 2. Technology and Implementation Research

I used ChatGPT and GitHub Copilot to research implementation choices before committing to them. This included questions about:
* FastAPI dependency injection
* SQLAlchemy sessions and transaction boundaries
* PostgreSQL constraints and data integrity
* Pydantic validation
* Password hashing and security
* Bearer-token authentication
* Authorization patterns
* Exception handling
* Testing strategies
* Logging
* Health checks
* Prometheus metrics
* Migrations

**Examples of questions I asked:**
* How should request-scoped database sessions be modeled in this FastAPI application?
* Where should validation live so the API remains thin without pushing all business rules into the handler layer?
* Which invariants should be enforced in the database, and which should be handled in the application layer?
* How should this service handle authorization boundaries without coupling domain logic to HTTP concerns?
* What error contract should the API expose without leaking internals or creating inconsistent client behavior?
* What should the application health endpoint actually validate for this service, and what is beyond the scope of a lightweight backend?

I used these discussions to improve my understanding before coding, but I made the final implementation choices myself.

---

### 3. Trade-off Analysis

A large part of my use of ChatGPT and GitHub Copilot was focused on distinguishing between real engineering problems, legitimate trade-offs, and personal preferences.

**Examples of questions I asked included:**
* Should I keep database access in the service layer, or introduce a repository layer?
* Should the service layer use functions or classes for this project?
* Is async database tooling justified here, or is sync SQLAlchemy a better fit for the scope?
* Should application exceptions carry HTTP status codes, or should that concern stay in the HTTP layer?
* Should validation live only in Pydantic, or do I also need checks in business logic?
* Should I rely on database constraints, explicit application checks, or both?
* How much observability is appropriate for a small service with a limited timebox?
* Is this abstraction solving a real problem, or is it adding complexity without enough payoff?

This was important because I did not want to adopt patterns simply because they are common in large production systems. I wanted to evaluate whether a pattern was justified by the actual requirements of this application.

---

### 4. Code and Architecture Review

After making my own design and implementation decisions, I used ChatGPT and GitHub Copilot as reviewers to challenge the trade-offs in my approach. I asked questions such as:
* Does this responsibility belong in this layer, or am I mixing concerns?
* Is this layer doing too much for the scope of the project?
* Could this create circular dependencies or unnecessary coupling?
* Is this abstraction actually adding value, or am I adding indirection for its own sake?
* Am I validating the right concern at the correct layer?
* Could this error handling leak internal details or obscure the public contract?
* Are there missing invariants or race conditions that I need to address?
* Is this endpoint doing more than HTTP handling?
* Am I duplicating logic that should be centralized?
The point was not to accept AI feedback uncritically, but to get another perspective on whether my design was sound and whether I was drifting into complexity or unclear responsibilities.

---

### 5. Debugging and Implementation Support

I also used ChatGPT and GitHub Copilot as debugging partners when I encountered problems during implementation. Rather than treating them as oracles, I used them to narrow down likely causes and test whether my own hypotheses were reasonable.

**Examples of debugging questions included:**
* What could cause this error?
* What should I verify first?
* Is this likely a dependency or configuration issue?
* Why is this SQLAlchemy behavior occurring?
* Why is this test failing?
* What assumptions should I confirm before changing the implementation?

I then validated the proposed explanations by running the app and tests, rather than assuming the AI diagnosis was correct.

---

### 6. Testing Strategy

I also used ChatGPT and GitHub Copilot to help shape the testing strategy, not to generate tests without context.

**Examples of testing questions I used:**
* What are the most important failure modes behind this behavior?
* What should I verify first before changing the implementation?
* Is this more likely a dependency issue, configuration issue, or application logic issue?
* Why is this SQLAlchemy behavior occurring in this specific flow?
* What is the most relevant test to run to confirm the root cause?
* Which assumptions need to be validated before I change the code?

The goal was to test meaningful application behavior and important failure paths, not to overfit to implementation details.

---

### 7. Documentation and Decision Tracking

ChatGPT and GitHub Copilot were also useful for helping me document the project’s decisions in a structured way. Instead of asking either tool to generate the whole application at once, I broke the work into smaller prompts and decision points, such as:
* Project structure
* Application foundation
* Database design
* Domain models
* Schemas
* Error handling
* Authentication
* Authorization
* Services
* API layer
* Testing
* Observability
* Final review

This allowed me to maintain a clear trail of:
* The questions I explored
* The trade-offs I considered
* The decisions I made
* The reasons behind those decisions

---

In short, ChatGPT and GitHub Copilot were tools for research, reasoning, critique, and debugging. They helped me think more clearly and faster, but the final responsibility for the design, implementation, and validation remained mine.

---

## Areas where ChatGPT and GitHub Copilot contributed significantly to the implementation

ChatGPT and GitHub Copilot contributed significantly in the areas where there were multiple valid implementation choices and where the real value came from evaluating engineering trade-offs rather than simply generating code.

The most meaningful contributions were in architecture, database design, error handling, authentication and authorization, testing, observability, debugging, and documentation.

### Architecture and separation of responsibilities

One of the most valuable contributions was helping me evaluate the application’s architecture before committing to a design.

I used ChatGPT and GitHub Copilot to compare a simple layered design with more elaborate patterns and to ask questions such as:

- Do I actually need a repository layer?
- What problem would Unit of Work solve here?
- Would a generic repository improve the project or simply add indirection?
- Should the service layer use classes or functions?
- Should business logic live in the service or API layer?
- Is this abstraction justified by a concrete requirement?

The key trade-off was between structural clarity and unnecessary complexity. For a larger application, some of these abstractions may be useful. For this project, they needed to justify the extra complexity within a limited delivery window.

ChatGPT and GitHub Copilot helped me test those assumptions and challenge my own thinking, while I remained responsible for the final design decision to keep the architecture deliberately simple.

### Database and domain modelling

These tools also contributed significantly to the design of the User, Dish, and Rating models.

I used them to reason through:

- primary and foreign keys
- relationships
- uniqueness
- nullability
- timestamps
- deletion behavior
- rating constraints
- indexing
- database-level integrity
- application-level validation
- race conditions

A particularly important topic was the distinction between application validation and database constraints.

For example, an application can check whether a user or rating already exists before inserting data, but that validation is not enough to guarantee uniqueness under concurrent requests. This is why the strongest design combines application-level validation for useful client-facing behavior with database constraints for final integrity enforcement.

That distinction directly shaped the model design and the error-handling strategy.

### Error handling

ChatGPT and GitHub Copilot were helpful in structuring the error-handling design.

I worked through questions such as:

- Which errors belong in the service layer?
- Should services raise HTTPException?
- Should application exceptions know about HTTP status codes?
- Where should database IntegrityError exceptions be translated?
- Should authentication and authorization errors use the same hierarchy?
- Where should unexpected exceptions be caught?
- Where should errors be logged?
- What information should be exposed to API clients?

This led to a cleaner separation between application/business errors and HTTP concerns. The service layer could identify conditions such as "dish not found" or "duplicate rating" without knowing anything about HTTP responses, while the API layer translated those domain errors into appropriate response codes.

This was a strong example of where the value came from reasoning about layer boundaries, not simply generating code for an error handler.

### Authentication and authorization

The security design also benefited from the discussion.

I used ChatGPT and GitHub Copilot to reason about:

- whether password hashing should be delegated to a dedicated utility or kept within the auth service boundary
- whether token claims should include only identity data or also role metadata for authorization checks
- whether token expiration should be treated as security enforcement, UX policy, or both
- whether verification belongs in a dependency layer, a service layer, or both depending on the access pattern
- whether the authenticated user should be resolved once per request or recomputed at each authorization boundary
- whether role checks should be enforced at the route layer, the service layer, or both
- whether 401 and 403 should be treated as transport-level authentication failures vs authorization policy violations in this API contract
- whether a small role-based gate is sufficient for this project or whether a more general permission model would create unnecessary abstraction
- whether the auth design should optimize for simple operational clarity or for long-term extensibility

The design trade-off was between centralizing security logic and avoiding an unnecessarily complex permissions framework. The result was a simple and appropriate authentication and authorization model that matched the project’s scope rather than introducing a generalized authorization system.

### Testing

ChatGPT and GitHub Copilot contributed significantly to the testing strategy by helping identify important behaviors and failure paths rather than generating test cases without context.

Examples included:

- whether duplicate-user registration should fail fast at the API boundary, the service layer, or the database constraint level
- whether a missing dish should produce a domain-level not-found error or a generic validation failure depending on the contract
- whether admin-only access should be enforced before or after the business operation to avoid leaking information or performing unnecessary work
- whether an unauthenticated request should be tested as a transport issue, an auth failure, or both depending on the endpoint contract
- whether a rating rule violation should be treated as a domain validation error, an integrity violation, or a combination of both
- which behaviors are best validated by database constraints versus service-level or API-level tests
- which failure paths are important enough to require integration coverage instead of unit-level assertions alone

They also helped clarify the difference between testing implementation details and testing observable behavior. The emphasis remained on validating meaningful application behavior and important failure paths.

### Observability

These tools were also useful for identifying the minimum practical observability needs for the project, including:

- application logging
- exception logging
- health checks
- database connectivity checks
- Prometheus metrics
- avoiding sensitive information in logs

The trade-off here was between introducing useful production awareness and wasting time building an observability layer that exceeded the scope of the assignment. The result was a lightweight but practical approach.

### Debugging

ChatGPT and GitHub Copilot also provided useful support during implementation when issues emerged.

Rather than asking them to rewrite large sections of the application, I typically used them to investigate specific problems and confirm what I should verify. This included:

- understanding failing tests
- diagnosing database connectivity issues
- reasoning about SQLAlchemy behavior
- resolving import or dependency problems
- checking FastAPI dependency behavior
- reviewing exception-handling flows

I still validated each suggestion by running the application and tests, rather than assuming the diagnosis was correct.

### Documentation and development process

ChatGPT and GitHub Copilot were also valuable in shaping the documentation and the development process itself.

I deliberately used prompts as a sequence of engineering decisions rather than a single request to generate the project. After deciding on the application structure, the next prompt used that structure as its context. The following prompt then relied on the database decision, then the domain model, then schemas, then error handling, then authentication, and so on.

This created a trail of:

- the problem I was solving
- the options I considered
- the trade-offs involved
- the recommendation I evaluated
- the decision I made
- the next implementation consequence

That made the documentation stronger because it showed not only what was built, but why the project evolved the way it did.

### Overall assessment

The most significant contribution from ChatGPT and GitHub Copilot was not code generation alone. Their biggest value was in accelerating analysis, revealing blind spots, challenging assumptions, comparing implementation options, clarifying trade-offs, improving debugging, and helping document the reasoning behind the final design.

I remained responsible for making the final decisions, implementing the code, reviewing the result, running the checks, and validating the behavior in the real application.
