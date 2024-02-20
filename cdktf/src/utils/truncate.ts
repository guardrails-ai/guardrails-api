import { createHash } from 'crypto';

/**
 * Takes a name and a maximum length and returns a string of that length.
 * If the name parameter's length is greater than the specified max length
 * it will be truncated and the last 8 characters will be replaced with the
 * last 8 characters of the md5 hash of the original value for name.
 * @param name - string
 * @param maxLength - number
 * @returns string
 */
export function truncate (name: string, maxLength: number): string {
  if (name.length > maxLength) {
    const hash = createHash('md5').update(name).digest('hex');

    // last 8 characters yields a 0.000005 chance of collision
    const semiHash = hash.substring(hash.length - 8);

    const truncName = name.substring(0, maxLength - 8);
    return `${truncName}${semiHash}`;
  } else {
    return name;
  }
}