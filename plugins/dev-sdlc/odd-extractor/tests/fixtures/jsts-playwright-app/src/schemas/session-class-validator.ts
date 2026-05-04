// SYNTHETIC TEST FIXTURE — class-validator session DTO.
// Module shape: ESM (TypeScript) + decorators.
import {
  IsEmail,
  IsNotEmpty,
  IsOptional,
  MinLength,
  MaxLength,
} from 'class-validator';

export interface SessionMetadata {
  ip?: string;
  userAgent?: string;
}

export class SessionLoginDto {
  @IsEmail()
  email!: string;

  @IsNotEmpty()
  @MinLength(8)
  @MaxLength(72)
  password!: string;

  @IsOptional()
  rememberMe?: boolean;
}

export class SessionMetadataDto {
  @IsOptional()
  ip?: string;

  @IsOptional()
  userAgent?: string;
}
