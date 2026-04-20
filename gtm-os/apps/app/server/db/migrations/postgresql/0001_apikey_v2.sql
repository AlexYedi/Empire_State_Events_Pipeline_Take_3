ALTER TABLE "apikey" ADD COLUMN IF NOT EXISTS "configId" text;--> statement-breakpoint
ALTER TABLE "apikey" ADD COLUMN IF NOT EXISTS "referenceId" text;--> statement-breakpoint
UPDATE "apikey" SET "referenceId" = "userId" WHERE "referenceId" IS NULL AND "userId" IS NOT NULL;--> statement-breakpoint
UPDATE "apikey" SET "configId" = 'default' WHERE "configId" IS NULL;--> statement-breakpoint
ALTER TABLE "apikey" ALTER COLUMN "userId" DROP NOT NULL;
