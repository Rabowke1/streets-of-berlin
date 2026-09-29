#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include <initializer_list>
#include "BrawlerPlayerController.generated.h"

/**
 * Fragt Tastatur und Gamepad direkt ab und leitet die Eingaben an die Spielfigur weiter.
 *
 *  Tastatur: WASD/Pfeile = Laufen, J = Schlag, K/Leertaste = Sprung, L = Spezial, I = Rueckschlag,
 *            Enter = Start/Pause
 *  Gamepad:  Stick/D-Pad, X = Schlag, A = Sprung, Y = Spezial, B = Rueckschlag, Start = Start/Pause
 */
UCLASS()
class STREETSOFBERLIN_API ABrawlerPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	ABrawlerPlayerController();

	virtual void BeginPlay() override;
	virtual void PlayerTick(float DeltaTime) override;

private:
	bool AnyJustPressed(std::initializer_list<FKey> Keys) const;
	bool AnyDown(std::initializer_list<FKey> Keys) const;
};
