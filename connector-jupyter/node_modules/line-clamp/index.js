const ELLIPSIS_CHARACTER = '\u2026'

function lineClamp (rootElement, lineCount, options) {
  rootElement.style.cssText +=
    'overflow:hidden;overflow-wrap:break-word;word-wrap:break-word'

  const maximumHeight =
    (lineCount || 1) *
    parseInt(window.getComputedStyle(rootElement).lineHeight, 10)

  // Exit if text does not overflow `rootElement`.
  if (rootElement.scrollHeight <= maximumHeight) {
    return false
  }

  return truncateElementNode(
    rootElement,
    rootElement,
    maximumHeight,
    (options && options.ellipsis) || ELLIPSIS_CHARACTER
  )
}

function truncateElementNode (
  element,
  rootElement,
  maximumHeight,
  ellipsisCharacter
) {
  const childNodes = element.childNodes
  let i = childNodes.length - 1
  while (i > -1) {
    const childNode = childNodes[i--]
    if (
      (childNode.nodeType === 1 &&
        truncateElementNode(
          childNode,
          rootElement,
          maximumHeight,
          ellipsisCharacter
        )) ||
      (childNode.nodeType === 3 &&
        truncateTextNode(
          childNode,
          rootElement,
          maximumHeight,
          ellipsisCharacter
        ))
    ) {
      return true
    }
    element.removeChild(childNode)
  }
  return false
}

function truncateTextNode (
  textNode,
  rootElement,
  maximumHeight,
  ellipsisCharacter
) {
  let lastIndexOfWhitespace
  let textContent = textNode.textContent
  while (textContent.length > 1) {
    lastIndexOfWhitespace = textContent.lastIndexOf(' ')
    if (lastIndexOfWhitespace === -1) {
      break
    }
    textNode.textContent = textContent.substring(0, lastIndexOfWhitespace)
    if (rootElement.scrollHeight <= maximumHeight) {
      textNode.textContent = textContent
      break
    }
    textContent = textNode.textContent
  }
  return truncateTextNodeByCharacter(
    textNode,
    rootElement,
    maximumHeight,
    ellipsisCharacter
  )
}

const TRAILING_WHITESPACE_AND_PUNCTUATION_REGEX = /[ .,;!?'‘’“”\-–—]+$/

function truncateTextNodeByCharacter (
  textNode,
  rootElement,
  maximumHeight,
  ellipsisCharacter
) {
  let textContent = textNode.textContent
  let length = textContent.length
  while (length > 1) {
    // Trim off one trailing character and any trailing punctuation and whitespace.
    textContent = textContent
      .substring(0, length - 1)
      .replace(TRAILING_WHITESPACE_AND_PUNCTUATION_REGEX, '')
    length = textContent.length
    textNode.textContent = textContent + ellipsisCharacter
    if (rootElement.scrollHeight <= maximumHeight) {
      return true
    }
  }
  return false
}

module.exports = lineClamp
