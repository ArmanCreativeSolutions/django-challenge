# django-challenge

The Volleyball Federation has decided to use an online ticket-selling platform for the upcoming season, and our company has been selected to implement it.

# Requirements

Our system should provide REST APIs for the following tasks:

- User signup and login
- Adding a new stadium
- Defining matches
- Defining seat arrangements for each match
- Buying seats for a match (No payment gateway needed), with the following considerations:
  1. **Limit Purchase per User:** A user can buy only 1 ticket per match (check for existing tickets and return `400 Bad Request` if already booked).
  2. **Prevent Double Booking (Concurrency):** Handle high-traffic race conditions using database locks (`select_for_update()`) or distributed locks (Redis lock).
  3. **Seat Caching:** Cache available seat maps in Redis to avoid overwhelming PostgreSQL during peak traffic.
  4. **Prevent Duplicate Clicks (Idempotency):** Support an `Idempotency-Key` header to prevent double booking from multi-clicking.
  5. **Safe Transactions:** Ensure all booking steps are executed inside `@transaction.atomic` for automatic rollback on failure.

# Implementation Details

We don't need a GUI for this system; you can use Django Admin.
Try to write your code as **reusable** and **readable** as possible. Also, don't forget to **document your code** and clearly state the reasons for your design decisions.
Using API documentation tools (e.g., Swagger/OpenAPI) is a plus.

Keep in mind that many people will try to buy tickets simultaneously. Ensure your solution can handle high traffic. If a full implementation is not simple enough to complete quickly, you can describe your proposed architecture in your documentation.

Please fork this repository and submit your work via Pull Request. Commits are important to us, so make sure to commit frequently with clear, descriptive commit messages.

## We all use AI. Don't be ashamed

Everyone uses AI for development, and we expect you to do the same. AI is an integral part of our workflow, and we care about how effectively you leverage it.

To ensure you are using it properly, please add a file named `ai.md` to your project root containing:

1. What AI tools and models did you use?
2. Explain the different stages of software development where you used AI assistance and how you used them.
3. Show us how you prompt: include your prompts, explain which stage you used them in, how you evaluated the output, and how you corrected any errors or misbehaviors.
4. Explain how you monitor and manage your token/usage budget.

*You can refer to `sample.ai.md` in the repository for the expected format. Note: `ai.md` is the only file we expect you to write entirely by yourself.*
