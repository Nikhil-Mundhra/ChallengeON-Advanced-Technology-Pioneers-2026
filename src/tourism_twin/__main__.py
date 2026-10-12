from tourism_twin.cli import main

# Guarded: multiprocessing's spawn start method re-imports the main module in every worker.
if __name__ == "__main__":
    main()
